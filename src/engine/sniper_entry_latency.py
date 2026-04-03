"""Latency-aware entry adapter for the legacy sniper engine."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Any

from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_policy import EntryPolicy
from src.trading.entry.entry_types import EntryDecision
from src.trading.entry.fallback_strategy import FallbackStrategy
from src.trading.entry.latency_monitor import LatencyMonitor
from src.trading.entry.normal_entry_builder import NormalEntryBuilder
from src.trading.entry.signal_snapshot import build_signal_snapshot
from src.trading.market.market_data_cache import MarketDataCache
from src.utils.logger import log_info


_CONFIG = EntryConfig()
_CACHE = MarketDataCache(stale_after_ms=_CONFIG.max_ws_age_ms_for_caution)
_CACHE_LOCK = threading.RLock()
_LATENCY_MONITOR = LatencyMonitor(_CONFIG)
_ENTRY_POLICY = EntryPolicy(_CONFIG)
_NORMAL_BUILDER = NormalEntryBuilder(_CONFIG)
_FALLBACK_BUILDER = FallbackStrategy(_CONFIG)


def _best_ask_bid_from_ws(ws_data: dict[str, Any] | None) -> tuple[int, int]:
    orderbook = (ws_data or {}).get("orderbook") or {}
    asks = orderbook.get("asks") or []
    bids = orderbook.get("bids") or []

    best_ask = 0
    best_bid = 0
    if asks:
        try:
            best_ask = int(float((asks[0] or {}).get("price", 0) or 0))
        except Exception:
            best_ask = 0
    if bids:
        try:
            best_bid = int(float((bids[0] or {}).get("price", 0) or 0))
        except Exception:
            best_bid = 0
    return best_ask, best_bid


def freeze_signal_reference(
    stock: dict[str, Any],
    *,
    signal_price: int,
    strategy_id: str,
    signal_time: datetime | None = None,
) -> tuple[int, datetime]:
    """Freeze the first trigger-time reference until the attempt resolves."""

    frozen_price = int(float(stock.get("entry_signal_price", 0) or 0))
    frozen_time = stock.get("entry_signal_time")
    frozen_strategy = str(stock.get("entry_signal_strategy_id", "") or "")

    if frozen_price > 0 and isinstance(frozen_time, datetime) and frozen_strategy == strategy_id:
        return frozen_price, frozen_time

    now = signal_time or datetime.now(UTC)
    stock["entry_signal_price"] = int(signal_price)
    stock["entry_signal_time"] = now
    stock["entry_signal_strategy_id"] = str(strategy_id)
    return int(signal_price), now


def clear_signal_reference(stock: dict[str, Any]) -> None:
    """Clear the frozen trigger-time reference after the attempt finishes."""

    for key in ("entry_signal_price", "entry_signal_time", "entry_signal_strategy_id"):
        stock.pop(key, None)


def evaluate_live_buy_entry(
    *,
    stock: dict[str, Any],
    code: str,
    ws_data: dict[str, Any] | None,
    strategy_id: str,
    planned_qty: int,
    signal_price: int,
    signal_strength: float = 0.0,
    signal_time: datetime | None = None,
    target_buy_price: int = 0,
) -> dict[str, Any]:
    """
    Evaluate whether the legacy live path should still attempt a new BUY.

    Notes:
    - Final truth still comes from the current websocket cache snapshot.
    - CAUTION submits the fallback bundle in the live engine as scout + main
      orders, while delayed receipts are reconciled through shared entry state.
    """

    latest_price = int(float((ws_data or {}).get("curr", 0) or 0))
    if latest_price <= 0 or planned_qty <= 0:
        return {
            "allowed": False,
            "decision": EntryDecision.REJECT_MARKET_CONDITION.value,
            "reason": "invalid_latest_price_or_qty",
            "latency_state": "DANGER",
            "order_price": 0,
        }

    frozen_price, frozen_time = freeze_signal_reference(
        stock,
        signal_price=int(signal_price),
        strategy_id=strategy_id,
        signal_time=signal_time,
    )
    best_ask, best_bid = _best_ask_bid_from_ws(ws_data)
    raw_received_at = (ws_data or {}).get("last_ws_update_ts")
    received_at = None if raw_received_at is None else float(raw_received_at)

    with _CACHE_LOCK:
        _CACHE.update(
            code,
            last_price=latest_price,
            best_ask=best_ask,
            best_bid=best_bid,
            received_at=received_at,
        )
        quote_health = _CACHE.get_quote_health(code)

    latency = _LATENCY_MONITOR.evaluate(
        ws_age_ms=quote_health.ws_age_ms,
        ws_jitter_ms=quote_health.ws_jitter_ms,
        order_rtt_avg_ms=0,
        order_rtt_p95_ms=0,
        quote_stale=quote_health.quote_stale,
        spread_ratio=quote_health.spread_ratio,
    )
    snapshot = build_signal_snapshot(
        symbol=code,
        strategy_id=strategy_id,
        signal_price=frozen_price,
        signal_strength=float(signal_strength),
        planned_qty=int(planned_qty),
        side="BUY",
        signal_time=frozen_time,
        context={
            "stock_name": stock.get("name"),
            "position_tag": stock.get("position_tag"),
        },
    )
    policy = _ENTRY_POLICY.evaluate(
        snapshot=snapshot,
        latency_status=latency,
        latest_price=latest_price,
        now=datetime.now(UTC),
    )

    result = {
        "allowed": False,
        "decision": policy.decision.value,
        "reason": policy.reason,
        "latency_state": latency.state.value,
        "latest_price": latest_price,
        "signal_price": frozen_price,
        "signal_time": frozen_time,
        "computed_allowed_slippage": policy.computed_allowed_slippage,
        "ws_age_ms": latency.ws_age_ms,
        "ws_jitter_ms": latency.ws_jitter_ms,
        "spread_ratio": latency.spread_ratio,
        "quote_stale": latency.quote_stale,
        "target_buy_price": int(target_buy_price or 0),
        "order_price": 0,
    }

    if policy.decision == EntryDecision.ALLOW_NORMAL:
        defensive_order = _NORMAL_BUILDER.build(snapshot=snapshot, latest_price=latest_price)
        order_price = int(defensive_order.price)
        if int(target_buy_price or 0) > 0:
            order_price = min(order_price, int(target_buy_price))
        result["allowed"] = True
        result["mode"] = "normal"
        result["order_price"] = order_price
        result["orders"] = [
            {
                "tag": "normal",
                "qty": int(snapshot.planned_qty),
                "price": order_price,
                "order_type": defensive_order.order_type,
                "tif": defensive_order.tif,
            }
        ]
        return result

    if policy.decision == EntryDecision.ALLOW_FALLBACK:
        fallback_orders = _FALLBACK_BUILDER.build(
            snapshot=snapshot,
            latest_price=latest_price,
            best_ask=best_ask,
        )
        result["allowed"] = True
        result["mode"] = "fallback"
        result["orders"] = [
            {
                "tag": order.tag,
                "qty": int(order.qty),
                "price": int(order.price),
                "order_type": order.order_type,
                "tif": order.tif,
            }
            for order in fallback_orders
            if int(order.qty) > 0
        ]
        log_info(
            f"[LATENCY_ENTRY_CAUTION] {stock.get('name')}({code}) "
            f"fallback_bundle_ready orders={len(result['orders'])}"
        )
        return result

    result["mode"] = "reject"
    return result
