from src.trading.entry.orderbook_stability_observer import OrderbookStabilityObserver


def test_flicker_rate_counts_reversion_within_10s():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=100.0)
    observer.record_quote("123456", best_bid=10_010, best_ask=10_020, ts=101.0)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=102.0)

    snapshot = observer.snapshot("123456", now=102.0)

    assert snapshot["fr_10s"] == 2
    assert snapshot["sample_quote_count"] == 3


def test_quote_age_percentiles_are_matched_to_previous_quote():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=100.0)
    observer.record_trade("123456", price=10_010, ts=100.1)
    observer.record_trade("123456", price=10_000, ts=100.5)

    snapshot = observer.snapshot("123456", now=100.5)

    assert snapshot["quote_age_p50_ms"] == 300.0
    assert snapshot["quote_age_p90_ms"] == 460.0
    assert snapshot["sample_trade_count"] == 2


def test_print_quote_alignment_accepts_spread_and_mid_plus_one_tick():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_050, ts=100.0)
    observer.record_trade("123456", price=10_020, ts=100.1)
    observer.record_trade("123456", price=10_035, ts=100.2)
    observer.record_trade("123456", price=10_100, ts=100.3)

    snapshot = observer.snapshot("123456", now=100.3)

    assert snapshot["print_quote_alignment"] == 0.666667
    assert snapshot["unstable_quote_observed"] is True
    assert "print_quote_alignment" in snapshot["unstable_reasons"]


def test_window_prunes_old_quote_trade_and_flicker_events():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=100.0)
    observer.record_quote("123456", best_bid=10_010, best_ask=10_020, ts=101.0)
    observer.record_quote("123456", best_bid=10_000, best_ask=10_010, ts=102.0)
    observer.record_trade("123456", price=10_010, ts=102.0)

    snapshot = observer.snapshot("123456", now=113.0)

    assert snapshot["fr_10s"] == 0
    assert snapshot["sample_quote_count"] == 0
    assert snapshot["sample_trade_count"] == 0
