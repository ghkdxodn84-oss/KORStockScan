import json
from pathlib import Path
from types import SimpleNamespace

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
    assert "calibration_candidates" in report
    assert "post_apply_attribution" in report
    assert "safety_guard_pack" in report
    assert "calibration_trigger_pack" in report
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
    whipsaw = report["threshold_snapshot"]["soft_stop_whipsaw_confirmation"]
    assert whipsaw["apply_ready"] is True
    whipsaw_candidate = next(
        item for item in report["calibration_candidates"] if item["family"] == "soft_stop_whipsaw_confirmation"
    )
    assert whipsaw_candidate["apply_mode"] == "calibrated_apply_candidate"
    assert whipsaw_candidate["calibration_state"] in {"adjust_up", "adjust_down", "hold"}
    assert whipsaw_candidate["safety_revert_required"] is False
    assert whipsaw_candidate["target_env_keys"]
    assert whipsaw_candidate["max_step_per_day"] is not None
    assert whipsaw_candidate["sample_window"] == "rolling_10d_with_daily_guard"
    assert whipsaw_candidate["window_policy"]["daily_only_allowed"] is False
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


def test_threshold_cycle_report_marks_calibration_sample_and_live_risk_states():
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [],
        report_source_loader=lambda target_date: {"sources": {}, "source_metrics": {}, "new_observation_axis_created": False},
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    assert candidates["soft_stop_whipsaw_confirmation"]["calibration_state"] == "hold_sample"
    assert candidates["soft_stop_whipsaw_confirmation"]["sample_floor_status"] == "hold_sample"
    assert candidates["soft_stop_whipsaw_confirmation"]["safety_revert_required"] is False
    assert candidates["trailing_continuation"]["calibration_state"] == "freeze"
    assert candidates["trailing_continuation"]["allowed_runtime_apply"] is False
    assert candidates["scale_in_price_guard"]["calibration_state"] == "hold_sample"
    assert candidates["scale_in_price_guard"]["allowed_runtime_apply"] is False
    assert candidates["scale_in_price_guard"]["apply_mode"] == "report_only_calibration"
    assert candidates["scale_in_price_guard"]["sample_window"] == "rolling_10d_or_cumulative_sparse"
    assert candidates["pre_submit_price_guard"]["calibration_state"] == "hold_sample"
    assert candidates["pre_submit_price_guard"]["allowed_runtime_apply"] is True
    assert candidates["liquidity_gate_refined_candidate"]["allowed_runtime_apply"] is False
    assert candidates["liquidity_gate_refined_candidate"]["apply_mode"] == "report_only_calibration"
    assert candidates["overbought_gate_refined_candidate"]["allowed_runtime_apply"] is False
    assert candidates["holding_flow_ofi_smoothing"]["sample_window"] == "daily_intraday"
    assert report["post_apply_attribution"]["soft_stop_balanced_policy"]["perfect_win_rate_required"] is False


def test_threshold_cycle_report_routes_entry_filter_ev_sources_to_calibration_families():
    report_sources = {
        "sources": {
            "missed_entry_counterfactual": {
                "path": "data/report/monitor_snapshots/missed_entry_counterfactual_2026-05-08.json",
                "exists": True,
            },
            "performance_tuning": {
                "path": "data/report/monitor_snapshots/performance_tuning_2026-05-08.json",
                "exists": True,
            },
        },
        "source_metrics": {
            "latency_guard_miss_ev_recovery": {
                "evaluated_candidates": 25,
                "missed_winner_rate": 70.0,
                "avoided_loser_rate": 20.0,
                "quote_fresh_latency_pass_rate": 90.0,
                "performance_latency_block_events": 25,
            },
            "buy_score65_74": {
                "score65_74_candidates": 3,
                "wait6579_total_candidates": 3,
                "blocked_ai_score_evaluated": 22,
                "blocked_ai_score_missed_winner_rate": 60.0,
                "blocked_ai_score_avoided_loser_rate": 20.0,
            },
            "liquidity_gate_refined_candidate": {
                "evaluated_candidates": 21,
                "missed_winner_rate": 45.0,
                "avoided_loser_rate": 35.0,
                "performance_blocked_liquidity_events": 21,
            },
            "overbought_gate_refined_candidate": {
                "evaluated_candidates": 21,
                "missed_winner_rate": 15.0,
                "avoided_loser_rate": 45.0,
                "performance_blocked_overbought_events": 21,
            },
        },
    }
    pipeline_rows = (
        [{"stage": "pre_submit_price_guard_block", "fields": {"price_below_bid_bps": "85"}} for _ in range(5)]
        + [{"stage": "blocked_liquidity", "fields": {}} for _ in range(5)]
        + [{"stage": "blocked_overbought", "fields": {}} for _ in range(5)]
        + [{"stage": "blocked_ai_score", "fields": {"ai_score": "70"}} for _ in range(5)]
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: pipeline_rows,
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    assert candidates["pre_submit_price_guard"]["calibration_state"] == "adjust_up"
    assert candidates["pre_submit_price_guard"]["source_metrics"]["missed_winner_rate"] == 70.0
    assert candidates["score65_74_recovery_probe"]["source_metrics"]["blocked_ai_score_evaluated"] == 22
    assert candidates["liquidity_gate_refined_candidate"]["calibration_state"] == "hold"
    assert candidates["liquidity_gate_refined_candidate"]["allowed_runtime_apply"] is False
    assert candidates["overbought_gate_refined_candidate"]["calibration_state"] == "freeze"


def test_threshold_cycle_calibration_uses_holding_exit_report_sources():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-04-30",
        "sources": {
            "holding_exit_observation": {"path": "data/report/monitor_snapshots/holding_exit_observation_2026-04-30.json", "exists": True},
            "holding_exit_sentinel": {"path": "data/report/holding_exit_sentinel/holding_exit_sentinel_2026-04-30.json", "exists": True},
        },
        "source_metrics": {
            "soft_stop": {
                "holding_exit_observation_total": 20,
                "holding_exit_observation_rebound_above_sell_10m_rate": 90.0,
                "holding_exit_observation_whipsaw_signal": True,
            },
            "holding_flow": {
                "sentinel_primary": "HOLD_DEFER_DANGER",
                "holding_flow_override_defer_exit": 67,
                "max_defer_worsen_pct": 0.8,
            },
            "trailing": {
                "evaluated_trailing": 17,
                "missed_upside_rate": 29.4,
                "good_exit_rate": 41.2,
            },
        },
        "new_observation_axis_created": False,
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
        calibration_run_phase="intraday",
    )

    assert report["meta"]["calibration_run_phase"] == "intraday"
    assert report["meta"]["calibration_cadence"] == "twice_daily_intraday_and_postclose"
    assert report["calibration_source_bundle"]["new_observation_axis_created"] is False
    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    assert candidates["soft_stop_whipsaw_confirmation"]["source_sample_count"] == 20
    assert candidates["soft_stop_whipsaw_confirmation"]["sample_floor_status"] == "ready"
    assert candidates["soft_stop_whipsaw_confirmation"]["window_policy"]["primary"] == "rolling_10d"
    assert candidates["soft_stop_whipsaw_confirmation"]["source_metrics"]["holding_exit_observation_whipsaw_signal"] is True
    assert candidates["holding_flow_ofi_smoothing"]["source_sample_count"] == 67
    assert candidates["holding_flow_ofi_smoothing"]["source_metrics"]["sentinel_primary"] == "HOLD_DEFER_DANGER"


def test_soft_stop_calibration_holds_on_single_post_sell_source_sample():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-08",
        "sources": {
            "post_sell_feedback": {"path": "data/report/monitor_snapshots/post_sell_feedback_2026-05-08.json", "exists": True},
        },
        "source_metrics": {
            "soft_stop": {
                "post_sell_soft_stop_total": 1,
                "post_sell_rebound_above_sell_10m_rate": 100.0,
                "post_sell_rebound_above_buy_10m_rate": 100.0,
                "post_sell_rebound_above_sell_30m_rate": 100.0,
                "post_sell_rebound_above_buy_30m_rate": 100.0,
                "post_sell_rebound_above_sell_60m_rate": 100.0,
                "post_sell_rebound_above_buy_60m_rate": 100.0,
            },
        },
        "new_observation_axis_created": False,
    }
    pipeline_rows = [
        {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.82", "held_sec": "40"}}
        for _ in range(13)
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: pipeline_rows,
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
        calibration_run_phase="intraday",
    )

    candidate = next(
        item for item in report["calibration_candidates"] if item["family"] == "soft_stop_whipsaw_confirmation"
    )
    assert candidate["source_sample_count"] == 1
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["sample_floor_status"] == "hold_sample"
    assert candidate["runtime_change"] is False
    assert candidate["source_metrics"]["post_sell_rebound_above_buy_30m_rate"] == 100.0


def test_ai_correction_clamps_out_of_bounds_value_without_runtime_change():
    calibration_report = {
        "date": "2026-05-08",
        "meta": {"calibration_run_phase": "intraday"},
        "calibration_candidates": [
            {
                "family": "holding_flow_ofi_smoothing",
                "threshold_version": "holding_flow_ofi_smoothing:manifest_only:ready",
                "current_value": 90,
                "recommended_value": 90,
                "min_value": 30,
                "max_value": 120,
                "max_step_per_day": 15,
                "sample_floor": 20,
                "sample_count": 30,
                "source_sample_count": 30,
                "calibration_state": "hold",
                "window_policy": {"primary": "daily_intraday", "secondary": ["rolling_5d"], "daily_only_allowed": True},
                "allowed_runtime_apply": True,
            }
        ],
    }
    ai_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "holding_flow_ofi_smoothing",
                "anomaly_type": "defer_cost_spike",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "adjust_up",
                    "proposed_value": 200,
                    "anomaly_route": "threshold_candidate",
                    "sample_window": "daily_intraday",
                },
                "correction_reason": "defer cost deteriorated intraday",
                "required_evidence": ["holding_exit_sentinel"],
                "risk_flags": ["defer_cost"],
            }
        ],
    }

    review = report_mod.build_threshold_cycle_ai_correction_report(calibration_report, ai_raw_response=ai_response)

    item = review["items"][0]
    assert review["ai_status"] == "parsed"
    assert item["guard_accepted"] is True
    assert item["guard_decision"]["effective_value"] == 105
    assert item["guard_decision"]["clamped"] is True
    assert item["runtime_change"] is False
    assert item["final_source_of_truth"] == "deterministic_calibration_guard"


def test_ai_correction_keeps_soft_stop_single_sample_as_hold_sample():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-08",
        "sources": {"post_sell_feedback": {"path": "post_sell_feedback_2026-05-08.json", "exists": True}},
        "source_metrics": {
            "soft_stop": {
                "post_sell_soft_stop_total": 1,
                "post_sell_rebound_above_sell_30m_rate": 100.0,
                "post_sell_rebound_above_buy_30m_rate": 100.0,
            },
        },
        "new_observation_axis_created": False,
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.82", "held_sec": "40"}}
            for _ in range(13)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
        calibration_run_phase="intraday",
    )
    ai_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "soft_stop_whipsaw_confirmation",
                "anomaly_type": "late_rebound",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "adjust_up",
                    "proposed_value": 80,
                    "anomaly_route": "threshold_candidate",
                    "sample_window": "rolling_10d",
                },
                "correction_reason": "single late rebound case",
                "required_evidence": ["rolling soft-stop tail"],
                "risk_flags": ["single_case"],
            }
        ],
    }

    review = report_mod.build_threshold_cycle_ai_correction_report(report, ai_raw_response=ai_response)
    item = next(item for item in review["items"] if item["family"] == "soft_stop_whipsaw_confirmation")

    assert item["guard_accepted"] is False
    assert item["guard_decision"]["effective_state"] == "hold_sample"
    assert "window_policy_blocks_single_case_live_candidate" in item["guard_reject_reason"]
    deterministic = next(
        candidate for candidate in report["calibration_candidates"] if candidate["family"] == "soft_stop_whipsaw_confirmation"
    )
    assert deterministic["calibration_state"] == "hold_sample"


def test_ai_correction_instrumentation_gap_excludes_threshold_candidate_review():
    calibration_report = {
        "date": "2026-05-08",
        "run_phase": "postclose",
        "calibration_candidates": [
            {
                "family": "score65_74_recovery_probe",
                "threshold_version": "score65_74_recovery_probe:ready",
                "current_value": False,
                "recommended_value": True,
                "min_value": None,
                "max_value": None,
                "max_step_per_day": None,
                "sample_floor": 20,
                "sample_count": 50,
                "source_sample_count": 50,
                "calibration_state": "adjust_up",
                "window_policy": {"primary": "daily_intraday", "secondary": ["rolling_5d"], "daily_only_allowed": True},
                "allowed_runtime_apply": True,
            }
        ],
    }
    ai_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "score65_74_recovery_probe",
                "anomaly_type": "partial_sample_zero",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "hold_sample",
                    "anomaly_route": "instrumentation_gap",
                    "sample_window": "daily_intraday",
                },
                "correction_reason": "partial fill provenance missing",
                "required_evidence": ["full/partial split"],
                "risk_flags": ["instrumentation_gap"],
            }
        ],
    }

    review = report_mod.build_threshold_cycle_ai_correction_report(calibration_report, ai_raw_response=ai_response)
    decision = review["items"][0]["guard_decision"]

    assert decision["guard_accepted"] is True
    assert decision["route_action"] == "exclude_from_threshold_candidate_review"
    assert decision["runtime_change"] is False


def test_ai_correction_parse_failure_keeps_deterministic_report_available():
    calibration_report = {
        "date": "2026-05-08",
        "run_phase": "intraday",
        "calibration_candidates": [
            {
                "family": "holding_flow_ofi_smoothing",
                "threshold_version": "holding_flow_ofi_smoothing:ready",
                "current_value": 90,
                "recommended_value": 90,
                "calibration_state": "hold",
                "allowed_runtime_apply": True,
            }
        ],
    }

    review = report_mod.build_threshold_cycle_ai_correction_report(
        calibration_report,
        ai_raw_response={"schema_version": 1, "corrections": [], "apply_now": True},
    )

    assert review["ai_status"] == "parse_rejected"
    assert review["items"][0]["ai_review_state"] == "unavailable"
    assert review["items"][0]["deterministic_state"] == "hold"
    assert review["items"][0]["runtime_change"] is False


def test_openai_threshold_ai_correction_uses_strict_schema_and_deep_model(monkeypatch):
    captured = {}

    class _FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text=json.dumps({"schema_version": 1, "corrections": []}))

    class _FakeOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key
            self.responses = _FakeResponses()

    monkeypatch.setattr(report_mod, "_load_threshold_ai_openai_keys", lambda: [("OPENAI_API_KEY", "test-key")])
    monkeypatch.setattr("openai.OpenAI", _FakeOpenAI)

    raw_response, status = report_mod._call_openai_threshold_ai_correction(
        {"calibration_candidates": [], "calibration_source_bundle": {}},
        run_phase="postclose",
    )

    assert json.loads(raw_response) == {"schema_version": 1, "corrections": []}
    assert status["provider"] == "openai"
    assert status["model"] == "gpt-5.5"
    assert status["reasoning_effort"] == "high"
    assert captured["model"] == "gpt-5.5"
    assert captured["reasoning"]["effort"] == "high"
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["name"] == "threshold_ai_correction_v1"
    assert captured["text"]["format"]["strict"] is True
    assert captured["text"]["format"]["schema"]["additionalProperties"] is False
    assert "Korean domain glossary" in captured["instructions"]
    assert "Return only JSON" in captured["instructions"]


def test_efficient_tradeoff_calibration_adds_entry_bad_entry_and_adm_candidates():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-07",
        "sources": {
            "buy_funnel_sentinel": {"path": "data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-07.json", "exists": True},
            "wait6579_ev_cohort": {"path": "data/report/monitor_snapshots/wait6579_ev_cohort_2026-05-07.json", "exists": True},
            "holding_exit_decision_matrix": {"path": "data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_2026-05-07.json", "exists": True},
            "statistical_action_weight": {"path": "data/report/statistical_action_weight/statistical_action_weight_2026-05-07.json", "exists": True},
        },
        "source_metrics": {
            "buy_score65_74": {
                "sentinel_primary": "UPSTREAM_AI_THRESHOLD",
                "sentinel_secondary": ["LATENCY_DROUGHT"],
                "score65_74_candidates": 191,
                "score65_74_avg_expected_ev_pct": 4.7,
                "score65_74_avg_close_10m_pct": 5.5,
                "full_samples": 181,
                "partial_samples": 0,
                "threshold_relaxation_approved": False,
                "partial_sample_zero_is_calibration_target": True,
                "budget_pass": 30,
                "order_bundle_submitted": 10,
            },
            "bad_entry": {
                "refined_candidate": 441,
                "soft_stop_tail_sample": 20,
                "holding_flow_override_defer_exit": 67,
                "sell_order_sent": 9,
                "sell_completed": 9,
            },
            "decision_support": {
                "matrix_version": "holding_exit_decision_matrix_v1_2026-05-07",
                "matrix_entries": 14,
                "matrix_non_clear_edge": 0,
                "matrix_no_clear_edge": 14,
                "saw_candidate_weight_source": 7,
                "saw_defensive_only_high_loss_rate": 4,
                "saw_insufficient_sample": 3,
            },
        },
        "new_observation_axis_created": False,
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-07",
        pipeline_loader=lambda target_date: [
            {"stage": "bad_entry_refined_candidate", "fields": {"would_exit": "True"}}
            for _ in range(12)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    assert candidates["score65_74_recovery_probe"]["apply_mode"] == "efficient_tradeoff_canary_candidate"
    assert candidates["score65_74_recovery_probe"]["calibration_state"] == "adjust_up"
    assert candidates["score65_74_recovery_probe"]["source_metrics"]["partial_samples"] == 0
    assert candidates["bad_entry_refined_canary"]["apply_mode"] == "efficient_tradeoff_canary_candidate"
    assert candidates["bad_entry_refined_canary"]["source_metrics"]["holding_flow_override_defer_exit"] == 67
    assert candidates["holding_exit_decision_matrix_advisory"]["calibration_state"] == "hold_no_edge"
    assert candidates["holding_exit_decision_matrix_advisory"]["apply_mode"] == "report_only_calibration"
    assert candidates["holding_exit_decision_matrix_advisory"]["sample_floor_status"] == "minimum_edge_missing"


def test_bad_entry_refined_candidate_waits_for_postclose_lifecycle_attribution(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "POST_SELL_DIR", tmp_path)
    (tmp_path / "post_sell_evaluations_2026-05-08.jsonl").write_text(
        json.dumps(
            {
                "recommendation_id": 5645,
                "outcome": "GOOD_EXIT",
                "exit_rule": "scalp_soft_stop_pct",
                "profit_rate": -1.75,
                "metrics_10m": {"mfe_pct": 0.713, "mae_pct": -11.058},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {
                "stage": "bad_entry_refined_candidate",
                "record_id": 5645,
                "fields": {
                    "exclusion_reason": "soft_stop_zone",
                    "would_exit": "False",
                    "should_exit": "False",
                },
            }
            for _ in range(10)
        ],
        report_source_loader=lambda target_date: {"sources": {}, "source_metrics": {}, "new_observation_axis_created": False},
        completed_rows_loader=lambda start_date, end_date: [],
    )

    family = report["threshold_snapshot"]["bad_entry_refined_canary"]
    lifecycle = family["sample"]["lifecycle_attribution"]
    assert lifecycle["post_sell_joined_records"] == 1
    assert lifecycle["final_type_counts"]["late_detected_soft_stop_zone"] == 1

    candidate = next(item for item in report["calibration_candidates"] if item["family"] == "bad_entry_refined_canary")
    assert candidate["calibration_state"] == "hold"
    assert candidate["source_metrics"]["post_sell_joined_candidate_records"] == 1
    assert candidate["source_metrics"]["late_detected_soft_stop_zone_records"] == 1
    assert candidate["runtime_change"] is False


def test_trade_lifecycle_attribution_splits_entry_holding_exit_and_post_sell_types(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "POST_SELL_DIR", tmp_path)
    (tmp_path / "post_sell_candidates_2026-05-08.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recommendation_id": 5645,
                        "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
                        "exit_rule": "scalp_soft_stop_pct",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "recommendation_id": 6001,
                        "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
                        "exit_rule": "scalp_trailing_take_profit",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "post_sell_evaluations_2026-05-08.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recommendation_id": 5645,
                        "outcome": "GOOD_EXIT",
                        "exit_rule": "scalp_soft_stop_pct",
                        "profit_rate": -1.75,
                        "metrics_10m": {"mfe_pct": 0.7, "mae_pct": -11.0},
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "recommendation_id": 6001,
                        "outcome": "MISSED_UPSIDE",
                        "exit_rule": "scalp_trailing_take_profit",
                        "profit_rate": 0.5,
                        "metrics_10m": {"mfe_pct": 2.2, "mae_pct": -0.3},
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {
                "stage": "order_bundle_submitted",
                "record_id": 5645,
                "stock_code": "298830",
                "stock_name": "슈어소프트테크",
                "emitted_at": "2026-05-08T12:53:39",
                "fields": {"entry_order_lifecycle": "normal", "entry_price_guard": "latency_danger_override_defensive"},
            },
            {
                "stage": "bad_entry_refined_candidate",
                "record_id": 5645,
                "emitted_at": "2026-05-08T12:59:40",
                "fields": {"exclusion_reason": "soft_stop_zone", "would_exit": "False"},
            },
            {
                "stage": "exit_signal",
                "record_id": 5645,
                "stock_code": "298830",
                "stock_name": "슈어소프트테크",
                "emitted_at": "2026-05-08T12:59:53",
                "fields": {
                    "exit_rule": "scalp_soft_stop_pct",
                    "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
                    "profit_rate": "-1.87",
                },
            },
            {
                "stage": "sell_completed",
                "record_id": 5645,
                "emitted_at": "2026-05-08T12:59:54",
                "fields": {"exit_rule": "scalp_soft_stop_pct", "profit_rate": "-1.75"},
            },
            {
                "stage": "order_bundle_submitted",
                "record_id": 6001,
                "stock_code": "000001",
                "stock_name": "트레일링",
                "emitted_at": "2026-05-08T10:00:00",
                "fields": {"entry_order_lifecycle": "normal"},
            },
            {
                "stage": "exit_signal",
                "record_id": 6001,
                "stock_code": "000001",
                "stock_name": "트레일링",
                "emitted_at": "2026-05-08T10:05:00",
                "fields": {
                    "exit_rule": "scalp_trailing_take_profit",
                    "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
                },
            },
            {
                "stage": "sell_completed",
                "record_id": 6001,
                "emitted_at": "2026-05-08T10:05:01",
                "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "0.5"},
            },
            {
                "stage": "order_bundle_submitted",
                "record_id": 7001,
                "stock_code": "000002",
                "stock_name": "미체결",
                "emitted_at": "2026-05-08T11:00:00",
                "fields": {"entry_order_lifecycle": "passive_probe"},
            },
            {
                "stage": "entry_order_cancel_confirmed",
                "record_id": 7001,
                "emitted_at": "2026-05-08T11:00:30",
                "fields": {"entry_order_lifecycle": "passive_probe"},
            },
        ],
        report_source_loader=lambda target_date: {"sources": {}, "source_metrics": {}, "new_observation_axis_created": False},
        completed_rows_loader=lambda start_date, end_date: [],
    )

    lifecycle = report["trade_lifecycle_attribution"]
    assert lifecycle["primary_type_counts"]["soft_stop_good_exit"] == 1
    assert lifecycle["primary_type_counts"]["trailing_early_exit"] == 1
    assert lifecycle["primary_type_counts"]["entry_unfilled_cancelled"] == 1
    assert lifecycle["family_views"]["bad_entry_refined"]["late_detected_soft_stop_zone"] == 1
    assert lifecycle["family_views"]["entry_price"]["entry_unfilled_cancelled"] == 1
    assert lifecycle["family_views"]["trailing"]["early_exit"] == 1


def test_scale_in_price_guard_calibration_uses_existing_sources_without_live_apply():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-07",
        "sources": {
            "holding_exit_sentinel": {
                "path": "data/report/holding_exit_sentinel/holding_exit_sentinel_2026-05-07.json",
                "exists": True,
            },
            "statistical_action_weight": {
                "path": "data/report/statistical_action_weight/statistical_action_weight_2026-05-07.json",
                "exists": True,
            },
        },
        "source_metrics": {
            "scale_in_price_guard": {
                "scale_in_price_resolved": 0,
                "scale_in_price_guard_block": 4,
                "scale_in_price_p2_observe": 0,
                "compact_scale_in_executed": 0,
                "avg_down_wait": 1,
                "pyramid_wait": 6,
            }
        },
        "new_observation_axis_created": False,
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-07",
        pipeline_loader=lambda target_date: [
            {
                "stage": "scale_in_price_guard_block",
                "fields": {
                    "add_type": "PYRAMID",
                    "reason": "micro_vwap_bp>60.0",
                    "spread_bps": "27.1",
                    "micro_vwap_bps": "70.0",
                },
            }
            for _ in range(4)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidate = next(item for item in report["calibration_candidates"] if item["family"] == "scale_in_price_guard")
    assert candidate["apply_mode"] == "report_only_calibration"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["runtime_change"] is False
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["sample_count"] == 7
    assert candidate["source_sample_count"] == 7
    assert candidate["source_metrics"]["compact_scale_in_executed"] == 0


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
    candidate = next(item for item in report["calibration_candidates"] if item["family"] == "scale_in_price_guard")
    assert candidate["apply_mode"] == "report_only_calibration"
    assert candidate["calibration_state"] == "hold"
    assert candidate["allowed_runtime_apply"] is False


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
