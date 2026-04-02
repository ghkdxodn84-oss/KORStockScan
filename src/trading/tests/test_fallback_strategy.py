from datetime import UTC, datetime

from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_types import SignalSnapshot
from src.trading.entry.fallback_strategy import FallbackStrategy


def _snapshot(planned_qty=10):
    return SignalSnapshot(
        symbol="005930",
        strategy_id="SCALP",
        signal_time=datetime.now(UTC),
        signal_price=10_000,
        signal_strength=0.9,
        planned_qty=planned_qty,
        side="BUY",
        context={},
    )


def test_fallback_one_share_mode():
    strategy = FallbackStrategy(EntryConfig(scout_qty_mode="ONE_SHARE", scout_min_qty=1))
    orders = strategy.build(snapshot=_snapshot(10), latest_price=10_020, best_ask=10_030)
    assert orders[0].qty == 1
    assert orders[1].qty == 9


def test_fallback_percent_mode():
    strategy = FallbackStrategy(EntryConfig(scout_qty_mode="PERCENT", scout_qty_percent=0.2, scout_min_qty=1))
    orders = strategy.build(snapshot=_snapshot(10), latest_price=10_020, best_ask=10_030)
    assert orders[0].qty == 2
    assert orders[1].qty == 8


def test_main_price_uses_more_conservative_anchor():
    strategy = FallbackStrategy(EntryConfig(fallback_main_defensive_ticks=2))
    orders = strategy.build(snapshot=_snapshot(10), latest_price=10_100, best_ask=10_110)
    scout_order, main_order = orders
    assert scout_order.price >= 10_110
    assert main_order.price < 10_000
