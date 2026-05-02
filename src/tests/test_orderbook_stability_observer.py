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


def test_orderbook_micro_qi_ofi_and_depth_normalization():
    observer = OrderbookStabilityObserver(window_sec=10)
    observer.record_quote(
        "123456",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=100,
        best_ask_qty=100,
        bid_depth_l=500,
        ask_depth_l=500,
        ts=100.0,
    )
    observer.record_quote(
        "123456",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=140,
        best_ask_qty=80,
        bid_depth_l=620,
        ask_depth_l=420,
        ts=101.0,
    )

    micro = observer.snapshot("123456", now=101.0)["orderbook_micro"]

    assert micro["ready"] is False
    assert micro["reason"] == "insufficient_samples"
    assert micro["qi"] == 0.636364
    assert micro["qi_ewma"] == 0.540909
    assert micro["ofi_instant"] == 60.0
    assert micro["ofi_ewma"] == 18.0
    assert micro["ofi_norm"] > 0
    assert micro["depth_ewma"] == 1012.0


def test_orderbook_micro_becomes_ready_after_min_samples_and_prunes_window():
    observer = OrderbookStabilityObserver(window_sec=10, micro_window_sec=2, micro_z_min_samples=3)
    observer.record_quote(
        "123456",
        best_bid=10_000,
        best_ask=10_010,
        best_bid_qty=100,
        best_ask_qty=100,
        bid_depth_l=500,
        ask_depth_l=500,
        ts=100.0,
    )
    for offset in range(1, 4):
        observer.record_quote(
            "123456",
            best_bid=10_000,
            best_ask=10_010,
            best_bid_qty=100 + offset,
            best_ask_qty=100,
            bid_depth_l=500 + offset,
            ask_depth_l=500,
            ts=100.0 + offset * 0.5,
        )

    ready_micro = observer.snapshot("123456", now=101.5)["orderbook_micro"]
    assert ready_micro["ready"] is True
    assert ready_micro["reason"] == "ready"
    assert ready_micro["micro_state"] in {"bullish", "neutral", "bearish"}
    assert ready_micro["ofi_z"] is not None

    pruned_micro = observer.snapshot("123456", now=104.0)["orderbook_micro"]
    assert pruned_micro["sample_quote_count"] == 0
    assert pruned_micro["ready"] is False
