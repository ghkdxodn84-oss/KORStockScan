import json
from pathlib import Path

from src.engine import daily_threshold_cycle_report as report_mod


def test_build_daily_threshold_cycle_report_generates_candidates_from_samples():
    pipeline_rows = {
        "2026-04-28": [],
        "2026-04-29": [],
        "2026-04-30": [
            {"stage": "budget_pass", "fields": {"signal_score": "72", "latest_strength": "111", "buy_pressure_10t": "53", "ws_age_ms": "900", "ws_jitter_ms": "410", "spread_ratio": "0.0078"}},
            {"stage": "budget_pass", "fields": {"signal_score": "74", "latest_strength": "114", "buy_pressure_10t": "56", "ws_age_ms": "980", "ws_jitter_ms": "430", "spread_ratio": "0.0080"}},
            {"stage": "budget_pass", "fields": {"signal_score": "76", "latest_strength": "118", "buy_pressure_10t": "58", "ws_age_ms": "1030", "ws_jitter_ms": "450", "spread_ratio": "0.0081"}},
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "71"}},
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "77"}},
            {"stage": "bad_entry_block_observed", "fields": {"held_sec": "65", "profit_rate": "-0.88", "peak_profit": "0.12", "ai_score": "41"}},
            {"stage": "bad_entry_block_observed", "fields": {"held_sec": "72", "profit_rate": "-0.94", "peak_profit": "0.18", "ai_score": "43"}},
            {"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.62", "held_sec": "88", "ai_score": "63", "ai_recovery_delta": "17"}},
            {"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.55", "held_sec": "94", "ai_score": "66", "ai_recovery_delta": "18"}},
            {"stage": "reversal_add_blocked_reason", "fields": {"reason": "hold_sec_out_of_range", "profit_rate": "-0.48", "held_sec": "210", "ai_score": "62", "ai_recovery_delta": "14"}},
            {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.74", "held_sec": "37"}},
            {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.95", "held_sec": "42"}},
        ]
        + [
            {"stage": "budget_pass", "fields": {"signal_score": "73", "latest_strength": "116", "buy_pressure_10t": "57", "ws_age_ms": "970", "ws_jitter_ms": "420", "spread_ratio": "0.0079"}}
            for _ in range(600)
        ]
        + [{"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}} for _ in range(25)]
        + [{"stage": "bad_entry_block_observed", "fields": {"held_sec": "70", "profit_rate": "-0.90", "peak_profit": "0.15", "ai_score": "42"}} for _ in range(30)]
        + [{"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.58", "held_sec": "92", "ai_score": "65", "ai_recovery_delta": "16"}} for _ in range(22)]
        + [{"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.82", "held_sec": "40"}} for _ in range(30)],
    }

    completed_rows = [
        {"profit_rate": -0.5, "buy_price": 8500, "buy_time": "2026-04-30 09:10:00", "daily_volume": 1_200_000},
        {"profit_rate": 0.3, "buy_price": 22000, "buy_time": "2026-04-30 10:05:00", "daily_volume": 3_000_000, "pyramid_count": 1},
        {"profit_rate": -1.1, "buy_price": 76000, "buy_time": "2026-04-30 14:20:00", "daily_volume": 8_000_000, "avg_down_count": 1},
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: pipeline_rows.get(target_date, []),
        completed_rows_loader=lambda start_date, end_date: completed_rows,
    )

    assert report["summary"]["completed_valid_rolling_7d"] == 3
    assert report["summary"]["loss_count_rolling_7d"] == 2
    assert "threshold_snapshot" in report
    assert "threshold_diff_report" in report
    assert "apply_candidate_list" in report
    assert "rollback_guard_pack" in report

    bad_entry = report["threshold_snapshot"]["bad_entry_block"]
    assert bad_entry["apply_ready"] is True

    pre_submit = report["threshold_snapshot"]["pre_submit_price_guard"]
    assert pre_submit["apply_ready"] is False
    assert 60 <= pre_submit["recommended"]["max_below_bid_bps"] <= 120

    soft_stop = report["threshold_snapshot"]["soft_stop_micro_grace"]
    assert soft_stop["apply_ready"] is True
    action_weight = report["threshold_snapshot"]["statistical_action_weight"]
    assert action_weight["apply_ready"] is False
    assert action_weight["recommended"]["data_completeness"]["price_known"] == 3

    apply_families = {item["family"] for item in report["apply_candidate_list"]}
    assert "pre_submit_price_guard" in apply_families or "entry_mechanical_momentum" in apply_families


def test_statistical_action_weight_report_buckets_completed_rows():
    completed_rows = [
        {
            "profit_rate": 0.8,
            "buy_price": 9000,
            "buy_time": "2026-04-30 09:10:00",
            "daily_volume": 1_000_000,
            "pyramid_count": 1,
        },
        {
            "profit_rate": 0.6,
            "buy_price": 9500,
            "buy_time": "2026-04-30 09:12:00",
            "daily_volume": 1_500_000,
            "pyramid_count": 1,
        },
        {
            "profit_rate": -0.7,
            "buy_price": 9500,
            "buy_time": "2026-04-30 09:16:00",
            "daily_volume": 1_200_000,
            "avg_down_count": 1,
        },
        {
            "profit_rate": 0.2,
            "buy_price": 22_000,
            "buy_time": "2026-04-30 10:05:00",
            "daily_volume": 6_000_000,
        },
        {
            "profit_rate": -0.3,
            "buy_price": 22_000,
            "buy_time": "2026-04-30 10:08:00",
            "daily_volume": 6_500_000,
        },
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [
            {"stage": "scale_in_executed", "fields": {"add_type": "PYRAMID"}},
            {"stage": "stat_action_decision_snapshot", "fields": {"chosen_action": "pyramid_wait"}},
            {"stage": "sell_completed", "fields": {"profit_rate": "0.8"}},
        ],
        completed_rows_loader=lambda start_date, end_date: completed_rows,
    )

    family = report["threshold_snapshot"]["statistical_action_weight"]
    assert family["sample"]["completed_valid"] == 5
    assert family["sample"]["pyramid_wait"] == 2
    assert family["sample"]["avg_down_wait"] == 1
    assert family["sample"]["compact_scale_in_executed"] == 1
    assert family["sample"]["compact_decision_snapshot"] == 1
    assert family["recommended"]["action_summary"]["pyramid_wait"]["avg_profit_rate"] == 0.7
    assert family["current"]["score_method"] == "empirical_bayes_lower_confidence_bound"
    first_price_bucket = family["recommended"]["by_price_bucket"][0]
    assert "best_confidence_adjusted_score" in first_price_bucket
    assert "policy_hint" in first_price_bucket
    assert family["recommended"]["data_completeness"]["volume_known"] == 5


def test_build_daily_threshold_cycle_report_keeps_unready_family_observe_only():
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [],
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=True,
    )

    reversal_add = report["threshold_snapshot"]["reversal_add"]
    assert reversal_add["apply_ready"] is False
    assert reversal_add["recommended"]["max_hold_sec"] >= 120

    assert report["apply_candidate_list"] == []
    assert any("skip-db" in warning for warning in report["warnings"])


def test_default_pipeline_loader_prefers_compact_threshold_file(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(report_mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    report_mod.THRESHOLD_CYCLE_DIR.mkdir(parents=True, exist_ok=True)

    compact_path = report_mod.THRESHOLD_CYCLE_DIR / "threshold_events_2026-04-30.jsonl"
    compact_path.write_text(
        json.dumps(
            {
                "event_type": "threshold_cycle_event",
                "stage": "bad_entry_block_observed",
                "fields": {"held_sec": "70", "profit_rate": "-0.8", "peak_profit": "0.1", "ai_score": "40"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    rows = report_mod._default_pipeline_loader("2026-04-30")
    assert len(rows) == 1
    assert rows[0]["stage"] == "bad_entry_block_observed"


def test_default_pipeline_loader_prefers_partitioned_compact_over_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(report_mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    partition_dir = report_mod.THRESHOLD_CYCLE_DIR / "date=2026-04-30" / "family=bad_entry_block"
    partition_dir.mkdir(parents=True, exist_ok=True)
    (partition_dir / "part-000001.jsonl").write_text(
        json.dumps(
            {
                "event_type": "threshold_cycle_event",
                "stage": "bad_entry_block_observed",
                "fields": {"held_sec": "70"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    report_mod.THRESHOLD_CYCLE_DIR.mkdir(parents=True, exist_ok=True)
    (report_mod.THRESHOLD_CYCLE_DIR / "threshold_events_2026-04-30.jsonl").write_text(
        json.dumps({"event_type": "threshold_cycle_event", "stage": "budget_pass", "fields": {}}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    checkpoint_dir = report_mod.THRESHOLD_CYCLE_DIR / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (checkpoint_dir / "2026-04-30.json").write_text(
        json.dumps({"completed": True, "paused_reason": None}, ensure_ascii=False),
        encoding="utf-8",
    )

    load_result = report_mod._default_pipeline_load_result("2026-04-30")
    assert [row["stage"] for row in load_result.rows] == ["bad_entry_block_observed"]
    assert load_result.meta["data_source"] == "partitioned_compact"
    assert load_result.meta["partition_count"] == 1
    assert load_result.meta["checkpoint_completed"] is True


def test_daily_threshold_cycle_report_includes_pipeline_load_meta(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(report_mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    partition_dir = report_mod.THRESHOLD_CYCLE_DIR / "date=2026-04-30" / "family=bad_entry_block"
    partition_dir.mkdir(parents=True, exist_ok=True)
    (partition_dir / "part-000001.jsonl").write_text(
        json.dumps({"event_type": "threshold_cycle_event", "stage": "bad_entry_block_observed", "fields": {}}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=True,
    )

    assert report["meta"]["pipeline_load"]["2026-04-30"]["data_source"] == "partitioned_compact"
    assert report["summary"]["event_count_same_day"] == 1


def test_statistical_action_weight_artifacts_render_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "STAT_ACTION_REPORT_DIR", tmp_path / "statistical_action_weight")
    monkeypatch.setattr(report_mod, "AI_DECISION_MATRIX_DIR", tmp_path / "holding_exit_decision_matrix")
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [
            {"stage": "stat_action_decision_snapshot", "fields": {"chosen_action": "exit_now"}},
            {"stage": "sell_completed", "fields": {"profit_rate": "0.4"}},
        ],
        completed_rows_loader=lambda start_date, end_date: [
            {
                "profit_rate": 0.8,
                "buy_price": 9000,
                "buy_time": "2026-04-30 09:10:00",
                "daily_volume": 1_000_000,
            },
            {
                "profit_rate": 0.6,
                "buy_price": 9000,
                "buy_time": "2026-04-30 09:12:00",
                "daily_volume": 1_000_000,
                "pyramid_count": 1,
            },
        ],
    )

    json_path, md_path = report_mod.save_statistical_action_weight_artifact(report)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["family"] == "statistical_action_weight"
    assert payload["runtime_change"] is False
    assert "Statistical Action Weight Report" in markdown
    assert "Price Bucket" in markdown
    assert "compact_decision_snapshot" in markdown


def test_holding_exit_decision_matrix_artifact_contains_prompt_hints(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "AI_DECISION_MATRIX_DIR", tmp_path / "holding_exit_decision_matrix")
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [],
        completed_rows_loader=lambda start_date, end_date: [
            {
                "profit_rate": 0.7,
                "buy_price": 9000,
                "buy_time": "2026-04-30 09:10:00",
                "daily_volume": 1_000_000,
            }
            for _ in range(8)
        ],
    )

    json_path, md_path = report_mod.save_holding_exit_decision_matrix(report)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["matrix_version"] == "holding_exit_decision_matrix_v1_2026-04-30"
    assert payload["runtime_change"] is False
    assert payload["hard_veto"]
    assert payload["entries"]
    assert "prompt_hint" in payload["entries"][0]
    assert "Holding/Exit Decision Matrix" in markdown
    assert "Prompt Hints" in markdown
