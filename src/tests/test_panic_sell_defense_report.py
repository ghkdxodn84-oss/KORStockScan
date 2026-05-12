import json
from datetime import datetime

from src.engine import panic_sell_defense_report as report_mod


TARGET_DATE = "2026-05-12"


def _event(
    hhmmss: str,
    *,
    stage: str = "exit_signal",
    record_id: int = 1,
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "HOLDING_PIPELINE",
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
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


def _write_json(path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _panic_rows() -> list[dict]:
    return [
        _event(
            f"10:{idx:02d}:00",
            record_id=idx,
            fields={"exit_rule": "scalp_soft_stop_loss", "profit_rate": "-2.5"},
        )
        for idx in range(5)
    ]


def test_normal_state_without_panic_threshold(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                fields={"exit_rule": "scalp_trailing_take_profit", "profit_rate": "1.2"},
            )
        ],
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"),
    )

    assert report["panic_state"] == "NORMAL"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert report["panic_metrics"]["panic_detected"] is False


def test_panic_sell_state_from_five_stop_losses_in_30_minutes(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "PANIC_SELL"
    assert report["panic_metrics"]["current_30m_stop_loss_exit_count"] == 5
    assert report["panic_metrics"]["panic_by_stop_loss_count"] is True
    freeze = next(item for item in report["canary_candidates"] if item["family"] == "panic_entry_freeze_guard")
    assert freeze["status"] == "report_only_candidate"
    assert freeze["allowed_runtime_apply"] is False


def test_recovery_watch_uses_active_sim_probe_average(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())
    _write_json(
        tmp_path / "runtime" / "scalp_live_simulator_state.json",
        {
            "owner": "scalp_ai_buy_all_live_simulator",
            "active_positions": [
                {
                    "stock_code": "000001",
                    "stock_name": "SIM1",
                    "buy_price": 10000,
                    "curr_price": 10110,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                {
                    "stock_code": "000002",
                    "stock_name": "SIM2",
                    "buy_price": 10000,
                    "curr_price": 10000,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            ],
        },
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "RECOVERY_WATCH"
    active = report["recovery_metrics"]["active_sim_probe"]
    assert active["avg_unrealized_profit_rate_pct"] == 0.55
    assert active["win_rate_pct"] == 50.0
    assert active["provenance_check"]["passed"] is True


def test_recovery_confirmed_keeps_probe_report_only_and_broker_forbidden(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())
    _write_json(
        tmp_path / "runtime" / "scalp_live_simulator_state.json",
        {
            "active_positions": [
                {
                    "stock_code": "000001",
                    "stock_name": "SIM1",
                    "buy_price": 10000,
                    "curr_price": 10160,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                {
                    "stock_code": "000002",
                    "stock_name": "SIM2",
                    "buy_price": 10000,
                    "curr_price": 10100,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                {
                    "stock_code": "000003",
                    "stock_name": "SIM3",
                    "buy_price": 10000,
                    "curr_price": 9990,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            ],
        },
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "RECOVERY_CONFIRMED"
    rebound = next(item for item in report["canary_candidates"] if item["family"] == "panic_rebound_probe")
    assert rebound["status"] == "report_only_candidate"
    assert rebound["allowed_runtime_apply"] is False
    assert rebound["provenance_check_passed"] is True
    assert report["policy"]["report_only"] is True


def test_hard_protect_emergency_exits_are_never_confirmation_eligible():
    hard_rows = [
        _event("10:00:00", fields={"exit_rule": "scalp_hard_stop_pct"}),
        _event("10:01:00", fields={"exit_rule": "protect_hard_stop"}),
        _event("10:02:00", fields={"exit_rule": "emergency_stop"}),
    ]
    eligible_rows = [
        _event("10:03:00", fields={"exit_rule": "scalp_soft_stop_loss"}),
        _event("10:04:00", fields={"exit_rule": "scalp_trailing_take_profit"}),
        _event("10:05:00", fields={"exit_rule": "holding_flow_override_defer_cost"}),
    ]

    assert all(report_mod.is_hard_protect_emergency_exit(row) for row in hard_rows)
    assert not any(report_mod.is_confirmation_eligible_exit(row) for row in hard_rows)
    assert all(report_mod.is_confirmation_eligible_exit(row) for row in eligible_rows)


def test_post_sell_feedback_is_separate_from_closed_pnl(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())
    _write_json(
        tmp_path / "report" / "monitor_snapshots" / f"post_sell_feedback_{TARGET_DATE}.json",
        {
            "soft_stop_forensics": {
                "total_soft_stop": 5,
                "rebound_above_sell_rate": {"10m": 40.0, "20m": 55.0},
                "rebound_above_buy_rate": {"10m": 12.0, "20m": 20.0},
            }
        },
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "RECOVERY_WATCH"
    assert report["panic_metrics"]["avg_exit_profit_rate_pct"] == -2.5
    post_sell = report["recovery_metrics"]["post_sell_feedback"]
    assert post_sell["rebound_above_sell_10_20m_pct"] == 55.0
    assert post_sell["rebound_above_buy_10_20m_pct"] == 20.0
