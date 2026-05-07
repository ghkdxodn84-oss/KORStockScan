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
            {"stage": "bad_entry_refined_candidate", "fields": {"exclusion_reason": "soft_stop_zone", "should_exit": "False"}},
            {"stage": "bad_entry_refined_candidate", "fields": {"exclusion_reason": "loss_too_shallow", "should_exit": "False"}},
            {"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.62", "held_sec": "88", "ai_score": "63", "ai_recovery_delta": "17"}},
            {"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.55", "held_sec": "94", "ai_score": "66", "ai_recovery_delta": "18"}},
            {
                "stage": "reversal_add_blocked_reason",
                "fields": {
                    "blocked_reason": "hold_sec_out_of_range",
                    "profit_rate": "-0.48",
                    "held_sec": "210",
                    "ai_score": "62",
                    "ai_recovery_delta": "14",
                    "pnl_ok": "True",
                    "hold_ok": "False",
                    "low_floor_ok": "True",
                    "ai_score_ok": "True",
                    "ai_recover_ok": "True",
                    "supply_ok": "True",
                    "buy_pressure_ok": "True",
                    "tick_accel_ok": "True",
                    "large_sell_absent_ok": "True",
                    "micro_vwap_ok": "True",
                },
            },
            {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.74", "held_sec": "37"}},
            {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.95", "held_sec": "42"}},
            {
                "stage": "stat_action_decision_snapshot",
                "record_id": 1001,
                "fields": {"chosen_action": "pyramid_wait", "scale_in_action_type": "PYRAMID"},
            },
            {
                "stage": "exit_signal",
                "record_id": 1001,
                "stock_code": "456040",
                "stock_name": "OCI",
                "emitted_at": "2026-04-30T09:47:37",
                "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "0.59", "peak_profit": "1.00", "current_ai_score": "62"},
            },
            {"stage": "sell_completed", "record_id": 1001, "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "0.59"}},
            {
                "stage": "stat_action_decision_snapshot",
                "record_id": 1002,
                "fields": {"chosen_action": "pyramid_wait", "scale_in_action_type": "PYRAMID"},
            },
            {
                "stage": "exit_signal",
                "record_id": 1002,
                "stock_code": "042370",
                "stock_name": "비츠로테크",
                "emitted_at": "2026-04-30T09:56:09",
                "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "2.79", "peak_profit": "3.48", "current_ai_score": "74"},
            },
            {"stage": "sell_completed", "record_id": 1002, "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "3.58"}},
        ]
        + [
            {"stage": "budget_pass", "fields": {"signal_score": "73", "latest_strength": "116", "buy_pressure_10t": "57", "ws_age_ms": "970", "ws_jitter_ms": "420", "spread_ratio": "0.0079"}}
            for _ in range(600)
        ]
        + [{"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}} for _ in range(25)]
        + [{"stage": "bad_entry_block_observed", "fields": {"held_sec": "70", "profit_rate": "-0.90", "peak_profit": "0.15", "ai_score": "42"}} for _ in range(30)]
        + [{"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.58", "held_sec": "92", "ai_score": "65", "ai_recovery_delta": "16"}} for _ in range(22)]
        + [{"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.82", "held_sec": "40"}} for _ in range(30)]
        + [
            {
                "stage": "protect_trailing_smooth_hold",
                "fields": {
                    "sample_span_sec": "10",
                    "sample_count": "4",
                    "below_ratio": "0.50",
                    "buffer_pct": "1.00",
                    "emergency_pct": "-2.00",
                },
            }
            for _ in range(12)
        ]
        + [
            {
                "stage": "protect_trailing_smooth_confirmed",
                "fields": {
                    "sample_span_sec": "12",
                    "sample_count": "4",
                    "below_ratio": "0.75",
                    "buffer_pct": "1.00",
                    "emergency_pct": "-2.00",
                },
            }
            for _ in range(10)
        ]
        + [
            {
                "stage": "sell_completed",
                "fields": {"exit_rule": "protect_trailing_stop", "profit_rate": "-0.20"},
            }
            for _ in range(2)
        ],
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
    assert bad_entry["sample"]["soft_stop_zone_candidate"] == 1

    reversal_add = report["threshold_snapshot"]["reversal_add"]
    assert reversal_add["sample"]["blocker_top"]["hold_sec_out_of_range"] == 1
    assert reversal_add["sample"]["near_miss_all_but_hold"] == 1

    pre_submit = report["threshold_snapshot"]["pre_submit_price_guard"]
    assert pre_submit["apply_ready"] is False
    assert 60 <= pre_submit["recommended"]["max_below_bid_bps"] <= 120

    soft_stop = report["threshold_snapshot"]["soft_stop_micro_grace"]
    assert soft_stop["apply_ready"] is True
    protect_trailing = report["threshold_snapshot"]["protect_trailing_smoothing"]
    assert protect_trailing["apply_ready"] is True
    assert protect_trailing["recommended"]["min_samples"] >= 3
    assert protect_trailing["recommended"]["buffer_pct"] == 1.0
    scalp_trailing = report["threshold_snapshot"]["scalp_trailing_take_profit"]
    assert scalp_trailing["sample"]["weak_borderline"] == 1
    assert scalp_trailing["sample"]["would_hold_if_weak_limit_plus_10bp"] == 1
    assert scalp_trailing["sample"]["would_hold_if_strong_ai_score_relaxed_5pt"] == 1
    assert scalp_trailing["sample"]["pyramid_signaled_not_executed"] == 2
    assert scalp_trailing["sample"]["borderline_examples"][0]["pyramid_state"] == "pyramid_signaled_not_executed"
    assert scalp_trailing["sample"]["strong_ai_boundary_examples"][0]["stock_code"] == "042370"
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


def test_statistical_action_weight_reports_eligible_but_not_chosen(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "POST_SELL_DIR", tmp_path)
    (tmp_path / "post_sell_evaluations_2026-04-30.jsonl").write_text(
        json.dumps(
            {
                "recommendation_id": 1001,
                "outcome": "MISSED_UPSIDE",
                "exit_rule": "scalp_soft_stop_pct",
                "profit_rate": -1.2,
                "metrics_10m": {"mfe_pct": 1.4, "mae_pct": -0.8},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [
            {
                "stage": "stat_action_decision_snapshot",
                "record_id": 1001,
                "stock_code": "000100",
                "fields": {
                    "chosen_action": "hold_wait",
                    "eligible_actions": "hold_wait|exit_now|pyramid_wait",
                    "rejected_actions": "exit_now:no_sell_signal",
                    "profit_rate": "-0.4",
                    "peak_profit": "0.2",
                    "drawdown_from_peak": "0.6",
                    "current_ai_score": "62",
                },
            }
        ],
        completed_rows_loader=lambda start_date, end_date: [],
    )

    eligible = report["threshold_snapshot"]["statistical_action_weight"]["recommended"]["eligible_but_not_chosen"]
    assert eligible["status"] == "report_only"
    assert eligible["sample_snapshots"] == 1
    assert eligible["sample_candidates"] == 2
    assert eligible["post_sell_joined_candidates"] == 2
    exit_row = next(row for row in eligible["action_summary"] if row["candidate_action"] == "exit_now")
    assert exit_row["avg_post_decision_mfe_10m_proxy"] == 1.4

    artifact = report_mod.build_statistical_action_weight_artifact(report)
    markdown = report_mod.render_statistical_action_weight_markdown(artifact)
    assert "Eligible But Not Chosen" in markdown
    assert "post_decision_*_proxy" in markdown


def test_ofi_ai_smoothing_families_generate_manifest_only_candidates():
    pipeline_rows = []
    for record_id in range(1, 7):
        pipeline_rows.append(
            {
                "stage": "entry_ai_price_ofi_skip_demoted",
                "record_id": record_id,
                "fields": {
                    "orderbook_micro_state": "neutral",
                    "entry_ai_price_ofi_regime": "neutral",
                    "orderbook_micro_snapshot_age_ms": "120",
                },
            }
        )
        pipeline_rows.append({"stage": "order_bundle_submitted", "record_id": record_id, "fields": {}})
        pipeline_rows.append({"stage": "sell_completed", "record_id": record_id, "fields": {"profit_rate": "0.20"}})
    pipeline_rows.extend(
        {
            "stage": "entry_ai_price_canary_skip_order",
            "fields": {
                "orderbook_micro_state": "bearish",
                "orderbook_micro_snapshot_age_ms": "130",
            },
        }
        for _ in range(15)
    )
    pipeline_rows.extend(
        {
            "stage": "entry_ai_price_canary_skip_followup",
            "fields": {"mfe_bps": "20", "mae_bps": "-10"},
        }
        for _ in range(3)
    )
    for record_id in range(101, 107):
        pipeline_rows.append(
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "record_id": record_id,
                "fields": {
                    "smoothing_action": "DEBOUNCE_EXIT",
                    "holding_flow_ofi_regime": "stable_bullish",
                    "orderbook_micro_state": "bullish",
                    "worsen_from_candidate": "0.10",
                },
            }
        )
        pipeline_rows.append({"stage": "sell_completed", "record_id": record_id, "fields": {"profit_rate": "0.30"}})
    for record_id in range(201, 216):
        pipeline_rows.append(
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "record_id": record_id,
                "fields": {
                    "smoothing_action": "CONFIRM_EXIT",
                    "holding_flow_ofi_regime": "stable_bearish",
                    "orderbook_micro_state": "bearish",
                    "worsen_from_candidate": "0.34",
                },
            }
        )
    pipeline_rows.append({"stage": "holding_flow_override_force_exit", "fields": {"force_reason": "worsen_floor"}})

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: pipeline_rows,
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=True,
    )

    entry_family = report["threshold_snapshot"]["entry_ofi_ai_smoothing"]
    assert entry_family["apply_ready"] is True
    assert entry_family["apply_mode"] == "manifest_only"
    assert entry_family["sample"]["demoted"] == 6
    assert entry_family["sample"]["demoted_submitted"] == 6
    assert entry_family["sample"]["demoted_completed"] == 6
    assert entry_family["recommended"]["entry_skip_demotion_confidence_upper"] == 90

    holding_family = report["threshold_snapshot"]["holding_flow_ofi_smoothing"]
    assert holding_family["apply_ready"] is True
    assert holding_family["apply_mode"] == "manifest_only"
    assert holding_family["sample"]["exit_debounce"] == 6
    assert holding_family["sample"]["bearish_confirm"] == 15
    assert holding_family["sample"]["force_exit_priority"] == 1
    assert holding_family["recommended"]["holding_bearish_confirm_worsen_pct"] == 0.3

    manifest_families = {
        item["family"]
        for item in report["apply_candidate_list"]
        if item["owner_rule"] == "manifest_only_no_runtime_mutation"
    }
    assert {"entry_ofi_ai_smoothing", "holding_flow_ofi_smoothing"} <= manifest_families


def test_scale_in_price_guard_family_generates_manifest_only_candidate():
    pipeline_rows = []
    for record_id in range(1, 13):
        pipeline_rows.append(
            {
                "stage": "scale_in_price_resolved",
                "record_id": record_id,
                "fields": {
                    "add_type": "PYRAMID",
                    "spread_bps": "42.5",
                    "micro_vwap_bps": "18.0",
                    "resolved_vs_curr_bps": "-12.0",
                    "effective_qty": "1",
                    "qty_reason": "pyramid_momentum_confirmed",
                },
            }
        )
        pipeline_rows.append({"stage": "scale_in_executed", "record_id": record_id, "fields": {"add_type": "PYRAMID"}})
    for record_id in range(101, 111):
        pipeline_rows.append(
            {
                "stage": "scale_in_price_guard_block",
                "record_id": record_id,
                "fields": {
                    "add_type": "PYRAMID",
                    "reason": "spread_too_wide",
                    "spread_bps": "91.0",
                    "micro_vwap_bps": "70.0",
                },
            }
        )
    for record_id in range(1, 4):
        pipeline_rows.append(
            {
                "stage": "scale_in_price_p2_observe",
                "record_id": record_id,
                "fields": {"add_type": "PYRAMID", "action": "SKIP"},
            }
        )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-06",
        pipeline_loader=lambda target_date: pipeline_rows,
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=True,
    )

    family = report["threshold_snapshot"]["scale_in_price_guard"]
    assert family["apply_ready"] is True
    assert family["apply_mode"] == "manifest_only"
    assert family["sample"]["resolved"] == 12
    assert family["sample"]["guard_block"] == 10
    assert family["sample"]["p2_observe"] == 3
    assert family["sample"]["block_reason"]["spread_too_wide"] == 10
    assert family["current"]["max_spread_bps"] == 80.0
    assert family["current"]["effective_qty_cap"] == 1

    manifest_families = {
        item["family"]
        for item in report["apply_candidate_list"]
        if item["owner_rule"] == "manifest_only_no_runtime_mutation"
    }
    assert "scale_in_price_guard" in manifest_families


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


def test_cumulative_threshold_cycle_report_splits_windows_and_cohorts():
    pipeline_rows = {
        "2026-04-29": [{"stage": "budget_pass", "fields": {"signal_score": "72"}}],
        "2026-04-30": [
            {"stage": "bad_entry_block_observed", "fields": {"held_sec": "70", "profit_rate": "-0.8"}},
            {"stage": "exit_signal", "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "0.6", "peak_profit": "1.0", "current_ai_score": "62"}},
        ],
    }
    completed_rows = [
        {"rec_date": "2026-04-28", "profit_rate": 0.4, "strategy": "SCALPING", "buy_price": 9000},
        {"rec_date": "2026-04-29", "profit_rate": -0.6, "strategy": "fallback_single", "buy_price": 9000},
        {"rec_date": "2026-04-30", "profit_rate": 1.2, "strategy": "SCALPING", "pyramid_count": 1, "last_add_type": "PYRAMID"},
        {"rec_date": "2026-04-30", "profit_rate": -0.9, "strategy": "SCALPING", "avg_down_count": 1, "last_add_type": "REVERSAL_ADD"},
        {"rec_date": "2026-04-30", "profit_rate": None, "strategy": "SCALPING"},
    ]

    report = report_mod.build_cumulative_threshold_cycle_report(
        "2026-04-30",
        start_date="2026-04-28",
        rolling_days=(2,),
        pipeline_loader=lambda target_date: pipeline_rows.get(target_date, []),
        completed_rows_loader=lambda start_date, end_date: completed_rows,
    )

    assert report["operator_decision"] == "report_only_review"
    assert report["source_flags"]["runtime_change"] is False
    assert report["summary"]["completed_valid_cumulative"] == 4
    assert report["completed_cohorts"]["cumulative"]["normal_only"]["sample"] == 3
    assert report["completed_cohorts"]["cumulative"]["pyramid_activated"]["sample"] == 1
    assert report["completed_cohorts"]["cumulative"]["reversal_add_activated"]["sample"] == 1
    assert report["completed_cohorts"]["rolling_2d"]["all_completed_valid"]["sample"] == 3
    assert report["summary"]["event_count_by_window"]["cumulative"] == 3
    assert "scalp_trailing_take_profit" in report["threshold_snapshot_by_window"]["rolling_2d"]
    assert report["apply_candidate_list_by_window"]["cumulative"] == []
    assert report["threshold_snapshot_by_window"]["cumulative"]["bad_entry_block"]["apply_mode"] == "report_only_reference"


def test_cumulative_threshold_cycle_report_artifacts_render_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "CUMULATIVE_THRESHOLD_REPORT_DIR", tmp_path / "threshold_cycle_cumulative")
    report = report_mod.build_cumulative_threshold_cycle_report(
        "2026-04-30",
        start_date="2026-04-30",
        rolling_days=(1,),
        pipeline_loader=lambda target_date: [{"stage": "budget_pass", "fields": {"signal_score": "72"}}],
        completed_rows_loader=lambda start_date, end_date: [
            {"rec_date": "2026-04-30", "profit_rate": 0.5, "strategy": "SCALPING", "buy_price": 9000},
        ],
    )

    json_path, md_path = report_mod.save_cumulative_threshold_cycle_report(report)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["source_flags"]["application_mode"] == "report_only_cumulative_threshold_input"
    assert payload["source_flags"]["live_threshold_mutation"] is False
    assert "Cumulative Threshold Cycle Report" in markdown
    assert "Cohort Summary" in markdown
    assert "runtime_change: `False`" in markdown
