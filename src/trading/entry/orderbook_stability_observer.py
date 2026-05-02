from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from math import sqrt
from statistics import median
from typing import Any

from src.trading.order.tick_utils import get_tick_size


DEFAULT_WINDOW_SEC = 10.0
DEFAULT_FR_THRESHOLD = 5
DEFAULT_AGE_P90_THRESHOLD_MS = 400.0
DEFAULT_ALIGNMENT_THRESHOLD = 0.90
DEFAULT_MICRO_LAMBDA = 0.3
DEFAULT_MICRO_WINDOW_SEC = 60.0
DEFAULT_MICRO_MAX_SAMPLES = 300
DEFAULT_MICRO_Z_MIN_SAMPLES = 20


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return default


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(float(ordered[0]), 3)
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return round(float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight), 3)


@dataclass
class _PendingReversion:
    side: str
    price: int
    changed_at: float
    counted: bool = False


@dataclass
class _SymbolState:
    quotes: deque[dict[str, Any]] = field(default_factory=deque)
    trades: deque[dict[str, Any]] = field(default_factory=deque)
    micro_samples: deque[dict[str, Any]] = field(default_factory=deque)
    pending_reversions: deque[_PendingReversion] = field(default_factory=deque)
    flicker_count: int = 0
    last_bid: int = 0
    last_ask: int = 0
    last_bid_qty: int = 0
    last_ask_qty: int = 0
    last_quote_ts: float = 0.0
    ofi_ewma: float = 0.0
    qi_ewma: float | None = None
    depth_ewma: float = 1.0
    last_ofi_instant: float = 0.0
    last_ofi_norm: float = 0.0
    last_ofi_z: float | None = None
    last_qi: float | None = None
    last_bid_depth: int = 0
    last_ask_depth: int = 0


class OrderbookStabilityObserver:
    """Observe short-window quote stability without affecting entry decisions."""

    def __init__(
        self,
        *,
        window_sec: float = DEFAULT_WINDOW_SEC,
        micro_window_sec: float = DEFAULT_MICRO_WINDOW_SEC,
        micro_max_samples: int = DEFAULT_MICRO_MAX_SAMPLES,
        micro_z_min_samples: int = DEFAULT_MICRO_Z_MIN_SAMPLES,
        micro_lambda: float = DEFAULT_MICRO_LAMBDA,
    ) -> None:
        self.window_sec = float(window_sec)
        self.micro_window_sec = float(micro_window_sec)
        self.micro_max_samples = int(micro_max_samples)
        self.micro_z_min_samples = int(micro_z_min_samples)
        self.micro_lambda = max(0.0, min(1.0, float(micro_lambda)))
        self._states: dict[str, _SymbolState] = {}
        self._lock = threading.RLock()

    def reset(self) -> None:
        with self._lock:
            self._states.clear()

    def record_quote(
        self,
        code: str,
        *,
        best_bid: int,
        best_ask: int,
        best_bid_qty: int = 0,
        best_ask_qty: int = 0,
        bid_depth_l: int = 0,
        ask_depth_l: int = 0,
        ts: float | None = None,
    ) -> None:
        safe_code = str(code or "").strip()[:6]
        if not safe_code:
            return
        now = float(ts if ts is not None else time.time())
        bid = _safe_int(best_bid)
        ask = _safe_int(best_ask)
        bid_qty = _safe_int(best_bid_qty)
        ask_qty = _safe_int(best_ask_qty)
        bid_depth = _safe_int(bid_depth_l) or bid_qty
        ask_depth = _safe_int(ask_depth_l) or ask_qty
        if bid <= 0 and ask <= 0:
            return
        with self._lock:
            state = self._states.setdefault(safe_code, _SymbolState())
            self._prune(state, now)
            previous_bid = state.last_bid
            previous_ask = state.last_ask
            if previous_bid > 0 and bid > 0 and bid != previous_bid:
                state.pending_reversions.append(_PendingReversion("bid", previous_bid, now))
            if previous_ask > 0 and ask > 0 and ask != previous_ask:
                state.pending_reversions.append(_PendingReversion("ask", previous_ask, now))

            state.last_bid = bid or previous_bid
            state.last_ask = ask or previous_ask
            self._update_orderbook_micro(
                state,
                now=now,
                bid=state.last_bid,
                ask=state.last_ask,
                bid_qty=bid_qty,
                ask_qty=ask_qty,
                bid_depth=bid_depth,
                ask_depth=ask_depth,
                previous_bid=previous_bid,
                previous_ask=previous_ask,
            )
            state.last_quote_ts = now
            state.quotes.append({"ts": now, "best_bid": state.last_bid, "best_ask": state.last_ask})
            self._mark_reversions(state, now)

    def record_trade(self, code: str, *, price: int, ts: float | None = None) -> None:
        safe_code = str(code or "").strip()[:6]
        if not safe_code:
            return
        now = float(ts if ts is not None else time.time())
        trade_price = _safe_int(price)
        if trade_price <= 0:
            return
        with self._lock:
            state = self._states.setdefault(safe_code, _SymbolState())
            self._prune(state, now)
            age_ms = None
            if state.last_quote_ts > 0:
                age_ms = max(0.0, (now - state.last_quote_ts) * 1000.0)
            aligned = self._is_aligned(trade_price, state.last_bid, state.last_ask)
            state.trades.append(
                {
                    "ts": now,
                    "price": trade_price,
                    "best_bid": state.last_bid,
                    "best_ask": state.last_ask,
                    "quote_age_ms": age_ms,
                    "aligned": aligned,
                }
            )

    def snapshot(self, code: str, *, now: float | None = None) -> dict[str, Any]:
        safe_code = str(code or "").strip()[:6]
        current = float(now if now is not None else time.time())
        with self._lock:
            state = self._states.setdefault(safe_code, _SymbolState())
            self._prune(state, current)
            ages = [float(t["quote_age_ms"]) for t in state.trades if t.get("quote_age_ms") is not None]
            aligned_values = [bool(t.get("aligned")) for t in state.trades if t.get("aligned") is not None]
            alignment = None
            if aligned_values:
                alignment = round(sum(1 for item in aligned_values if item) / len(aligned_values), 6)
            p50 = round(float(median(ages)), 3) if ages else None
            p90 = _percentile(ages, 0.90)
            reasons: list[str] = []
            if state.flicker_count > DEFAULT_FR_THRESHOLD:
                reasons.append("fr_10s")
            if p90 is not None and p90 > DEFAULT_AGE_P90_THRESHOLD_MS:
                reasons.append("quote_age_p90")
            if alignment is not None and alignment < DEFAULT_ALIGNMENT_THRESHOLD:
                reasons.append("print_quote_alignment")
            return {
                "fr_10s": int(state.flicker_count),
                "quote_age_p50_ms": p50,
                "quote_age_p90_ms": p90,
                "print_quote_alignment": alignment,
                "unstable_quote_observed": bool(reasons),
                "unstable_reasons": ",".join(reasons),
                "best_bid": int(state.last_bid or 0),
                "best_ask": int(state.last_ask or 0),
                "sample_trade_count": len(state.trades),
                "sample_quote_count": len(state.quotes),
                "orderbook_micro": self._micro_snapshot(state),
            }

    def _prune(self, state: _SymbolState, now: float) -> None:
        cutoff = now - self.window_sec
        while state.quotes and float(state.quotes[0].get("ts", 0.0)) < cutoff:
            state.quotes.popleft()
        while state.trades and float(state.trades[0].get("ts", 0.0)) < cutoff:
            state.trades.popleft()
        while state.pending_reversions and state.pending_reversions[0].changed_at < cutoff:
            old = state.pending_reversions.popleft()
            if old.counted and state.flicker_count > 0:
                state.flicker_count -= 1
        micro_cutoff = now - self.micro_window_sec
        while state.micro_samples and float(state.micro_samples[0].get("ts", 0.0)) < micro_cutoff:
            state.micro_samples.popleft()
        while len(state.micro_samples) > self.micro_max_samples:
            state.micro_samples.popleft()

    def _mark_reversions(self, state: _SymbolState, now: float) -> None:
        for item in state.pending_reversions:
            if item.counted:
                continue
            if now - item.changed_at > self.window_sec:
                continue
            current_price = state.last_bid if item.side == "bid" else state.last_ask
            if current_price == item.price:
                item.counted = True
                state.flicker_count += 1

    @staticmethod
    def _is_aligned(price: int, best_bid: int, best_ask: int) -> bool | None:
        if price <= 0 or best_bid <= 0 or best_ask <= 0:
            return None
        lower = min(best_bid, best_ask)
        upper = max(best_bid, best_ask)
        if lower <= price <= upper:
            return True
        mid = (best_bid + best_ask) / 2.0
        return abs(price - mid) <= get_tick_size(price)

    def _update_orderbook_micro(
        self,
        state: _SymbolState,
        *,
        now: float,
        bid: int,
        ask: int,
        bid_qty: int,
        ask_qty: int,
        bid_depth: int,
        ask_depth: int,
        previous_bid: int,
        previous_ask: int,
    ) -> None:
        previous_bid_qty = state.last_bid_qty
        previous_ask_qty = state.last_ask_qty
        has_previous = previous_bid > 0 and previous_ask > 0

        ofi_instant = 0.0
        if has_previous:
            if bid > previous_bid:
                ofi_instant += bid_qty
            elif bid < previous_bid:
                ofi_instant -= previous_bid_qty
            else:
                ofi_instant += bid_qty - previous_bid_qty

            if ask < previous_ask:
                ofi_instant -= ask_qty
            elif ask > previous_ask:
                ofi_instant += previous_ask_qty
            else:
                ofi_instant += previous_ask_qty - ask_qty

        depth_total = max(int(bid_depth) + int(ask_depth), 1)
        lam = self.micro_lambda
        first_micro_sample = len(state.micro_samples) == 0
        if first_micro_sample:
            state.ofi_ewma = float(ofi_instant)
            state.depth_ewma = float(depth_total)
        else:
            state.ofi_ewma = lam * ofi_instant + (1.0 - lam) * state.ofi_ewma
            state.depth_ewma = lam * depth_total + (1.0 - lam) * max(state.depth_ewma, 1.0)

        qi_denominator = bid_qty + ask_qty
        qi = (bid_qty / qi_denominator) if qi_denominator > 0 else None
        if qi is not None:
            state.qi_ewma = qi if state.qi_ewma is None else lam * qi + (1.0 - lam) * state.qi_ewma

        ofi_norm = state.ofi_ewma / sqrt(max(state.depth_ewma, 1.0))
        state.micro_samples.append({"ts": now, "ofi_norm": ofi_norm})
        state.last_ofi_instant = float(ofi_instant)
        state.last_ofi_norm = float(ofi_norm)
        state.last_ofi_z = self._ofi_z(state)
        state.last_qi = qi
        state.last_bid_qty = bid_qty
        state.last_ask_qty = ask_qty
        state.last_bid_depth = bid_depth
        state.last_ask_depth = ask_depth

    def _ofi_z(self, state: _SymbolState) -> float | None:
        values = [float(item.get("ofi_norm", 0.0)) for item in state.micro_samples]
        if len(values) < self.micro_z_min_samples:
            return None
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        std = sqrt(variance)
        if std <= 1e-9:
            return 0.0
        return (state.last_ofi_norm - mean) / std

    def _micro_snapshot(self, state: _SymbolState) -> dict[str, Any]:
        sample_count = len(state.micro_samples)
        reason = ""
        ready = True
        if state.last_qi is None or state.qi_ewma is None:
            ready = False
            reason = "missing_best_qty"
        elif sample_count < self.micro_z_min_samples or state.last_ofi_z is None:
            ready = False
            reason = "insufficient_samples"

        micro_state = "insufficient"
        if ready:
            ofi_z = float(state.last_ofi_z or 0.0)
            qi_ewma = float(state.qi_ewma or 0.0)
            if ofi_z >= 1.2 and qi_ewma >= 0.55:
                micro_state = "bullish"
            elif ofi_z <= -1.0 and qi_ewma < 0.48:
                micro_state = "bearish"
            else:
                micro_state = "neutral"

        return {
            "ready": bool(ready),
            "reason": reason or "ready",
            "qi": round(float(state.last_qi), 6) if state.last_qi is not None else None,
            "qi_ewma": round(float(state.qi_ewma), 6) if state.qi_ewma is not None else None,
            "ofi_instant": round(float(state.last_ofi_instant), 6),
            "ofi_ewma": round(float(state.ofi_ewma), 6),
            "ofi_norm": round(float(state.last_ofi_norm), 6),
            "ofi_z": round(float(state.last_ofi_z), 6) if state.last_ofi_z is not None else None,
            "depth_ewma": round(float(state.depth_ewma), 6),
            "micro_state": micro_state,
            "sample_quote_count": sample_count,
            "bid_depth_l": int(state.last_bid_depth or 0),
            "ask_depth_l": int(state.last_ask_depth or 0),
        }


ORDERBOOK_STABILITY_OBSERVER = OrderbookStabilityObserver()
