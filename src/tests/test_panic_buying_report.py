import json
from datetime import datetime

from src.engine import panic_buying_report as report_mod


TARGET_DATE = "2026-05-13"


def _event(
    hhmmss: str,
    *,
    stage: str = "orderbook_stability_observed",
    pipeline: str = "ENTRY_PIPELINE",
    record_id: int = 1,
    stock_code: str = "000001",
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": stock_code,
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{TARGET_DATE}T{hhmmss}",
        "emitted_date": TARGET_DATE,
    }


def _write_events(tmp_path, rows: list[dict]) -> None:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    with (event_dir / f"pipeline_events_{TARGET_DATE}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _micro_event(hhmmss: str, *, close: float, volume: float = 100.0, buy: float = 52.0, sell: float = 48.0, **fields):
    payload = {
        "curr_price": close,
        "open": fields.pop("open", close),
        "high": fields.pop("high", close),
        "low": fields.pop("low", close),
        "volume": volume,
        "buy_exec_volume": buy,
        "sell_exec_volume": sell,
        **fields,
    }
    return _event(hhmmss, fields=payload)


def test_normal_state_without_panic_buying_threshold(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=100.1),
            _micro_event("10:02:00", close=100.2),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:03:00"),
    )

    assert report["panic_buy_state"] == "NORMAL"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert report["panic_buy_metrics"]["panic_buy_active_count"] == 0


def test_microstructure_detector_adds_report_only_runner_flags(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=100.0),
            _micro_event(
                "10:02:00",
                close=102.6,
                open=100.0,
                high=102.8,
                low=99.9,
                volume=430,
                buy=76,
                sell=24,
                best_bid=10250,
                best_ask=10260,
                bid_depth_l5=1300,
                ask_depth_l5=520,
                ask_depth_drop_ratio=0.48,
                bid_depth_support_ratio=1.30,
                panic_buy_spread_ratio=2.0,
                orderbook_micro_ofi_z=3.0,
                orderbook_micro_qi_ewma=0.68,
                orderbook_micro_state="bullish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
            _micro_event(
                "10:03:00",
                close=103.2,
                open=102.5,
                high=103.4,
                low=102.4,
                volume=440,
                buy=75,
                sell=25,
                best_bid=10310,
                best_ask=10320,
                bid_depth_l5=1350,
                ask_depth_l5=500,
                ask_depth_drop_ratio=0.50,
                bid_depth_support_ratio=1.35,
                panic_buy_spread_ratio=2.1,
                orderbook_micro_ofi_z=3.1,
                orderbook_micro_qi_ewma=0.70,
                orderbook_micro_state="bullish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:04:00"),
    )

    micro = report["microstructure_detector"]
    assert report["panic_buy_state"] == "PANIC_BUY"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert micro["panic_buy_active_count"] == 1
    assert micro["allow_tp_override_count"] == 1
    assert micro["allow_runner_count"] == 1
    assert micro["latest_signals"][0]["allow_tp_override"] is True
    assert micro["policy"]["does_not_submit_orders"] is True
    assert micro["micro_cusum_observer"]["decision_authority"] == "source_quality_only"
    assert micro["micro_cusum_observer"]["consensus_pass_symbol_count"] == 1
    assert "order_submit" in micro["micro_cusum_observer"]["forbidden_uses"]
    assert all(item["allowed_runtime_apply"] is False for item in report["canary_candidates"])


def test_tp_counterfactual_does_not_create_order_decision(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                pipeline="HOLDING_PIPELINE",
                stage="exit_signal",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "peak_profit": "1.8",
                    "actual_order_submitted": "True",
                },
            )
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:01:00"),
    )

    tp = report["tp_counterfactual_summary"]
    assert tp["tp_like_exit_count"] == 1
    assert tp["trailing_winner_count"] == 1
    assert tp["policy"]["runtime_effect"] == "counterfactual_only_no_order_change"
    assert report["canary_candidates"][0]["family"] == "panic_buy_runner_tp_canary"
    assert report["canary_candidates"][0]["allowed_runtime_apply"] is False


def test_tp_counterfactual_propagates_non_real_sibling_to_sparse_exit(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                pipeline="HOLDING_PIPELINE",
                stage="exit_signal",
                record_id=0,
                stock_code="042700",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "peak_profit": "1.8",
                },
            ),
            _event(
                "10:00:01",
                pipeline="HOLDING_PIPELINE",
                stage="scalp_sim_sell_order_assumed_filled",
                record_id=0,
                stock_code="042700",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "peak_profit": "1.8",
                    "simulated_order": "true",
                    "actual_order_submitted": "false",
                    "simulation_book": "scalp_ai_buy_all",
                },
            ),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:01:00"),
    )

    tp = report["tp_counterfactual_summary"]
    assert tp["real_exit_count"] == 0
    assert tp["non_real_exit_count"] == 2
    assert tp["tp_like_exit_count"] == 0
    assert tp["non_real_tp_like_exit_count"] == 2
