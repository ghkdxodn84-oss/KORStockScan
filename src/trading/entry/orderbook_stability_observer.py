from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from statistics import median
from typing import Any

from src.trading.order.tick_utils import get_tick_size


DEFAULT_WINDOW_SEC = 10.0
DEFAULT_FR_THRESHOLD = 5
DEFAULT_AGE_P90_THRESHOLD_MS = 400.0
DEFAULT_ALIGNMENT_THRESHOLD = 0.90


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
    pending_reversions: deque[_PendingReversion] = field(default_factory=deque)
    flicker_count: int = 0
    last_bid: int = 0
    last_ask: int = 0
    last_quote_ts: float = 0.0


class OrderbookStabilityObserver:
    """Observe short-window quote stability without affecting entry decisions."""

    def __init__(self, *, window_sec: float = DEFAULT_WINDOW_SEC) -> None:
        self.window_sec = float(window_sec)
        self._states: dict[str, _SymbolState] = {}
        self._lock = threading.RLock()

    def reset(self) -> None:
        with self._lock:
            self._states.clear()

    def record_quote(self, code: str, *, best_bid: int, best_ask: int, ts: float | None = None) -> None:
        safe_code = str(code or "").strip()[:6]
        if not safe_code:
            return
        now = float(ts if ts is not None else time.time())
        bid = _safe_int(best_bid)
        ask = _safe_int(best_ask)
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


ORDERBOOK_STABILITY_OBSERVER = OrderbookStabilityObserver()
