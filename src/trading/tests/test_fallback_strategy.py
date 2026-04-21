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


def test_fallback_strategy_is_deprecated_null_object():
    strategy = FallbackStrategy(EntryConfig(scout_qty_mode="ONE_SHARE", scout_min_qty=1))
    orders = strategy.build(snapshot=_snapshot(10), latest_price=10_020, best_ask=10_030)
    assert orders == []


def test_fallback_strategy_does_not_restore_scout_main_from_config():
    strategy = FallbackStrategy(EntryConfig(scout_qty_mode="ONE_SHARE", scout_min_qty=1))
    orders = strategy.build(snapshot=_snapshot(10), latest_price=10_020, best_ask=10_030)
    assert orders == []


def test_fallback_percent_mode_is_deprecated():
    strategy = FallbackStrategy(EntryConfig(scout_qty_mode="PERCENT", scout_qty_percent=0.2, scout_min_qty=1))
    orders = strategy.build(snapshot=_snapshot(10), latest_price=10_020, best_ask=10_030)
    assert orders == []


def test_deprecated_fallback_ignores_price_anchors():
    strategy = FallbackStrategy(EntryConfig(fallback_main_defensive_ticks=2))
    orders = strategy.build(snapshot=_snapshot(10), latest_price=10_100, best_ask=10_110)
    assert orders == []
