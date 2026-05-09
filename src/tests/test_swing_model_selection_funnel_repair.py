import json
import sys
from pathlib import Path

import pandas as pd

from src.engine.swing_selection_funnel_report import (
    build_swing_selection_funnel_report,
    summarize_pipeline_events,
)
from src.engine.swing_daily_simulation_report import (
    build_swing_daily_simulation_report,
    filter_live_recommendations,
    simulate_swing_recommendations,
)
from src.engine.swing_lifecycle_audit import (
    build_swing_improvement_automation_report,
    build_swing_lifecycle_audit_report,
    build_swing_threshold_ai_review_report,
    write_swing_lifecycle_outputs,
)
from src.model import common_v2
from src.model.common_v2 import daily_selection_stats, select_daily_candidates
from src.scanners.final_ensemble_scanner import classify_v2_csv_pick


def _score_rows():
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-05-08"),
                "code": "000001",
                "name": "A",
                "bull_regime": 1,
                "hybrid_mean": 0.36,
                "score": 0.10,
            },
            {
                "date": pd.Timestamp("2026-05-08"),
                "code": "000002",
                "name": "B",
                "bull_regime": 1,
                "hybrid_mean": 0.34,
                "score": 0.90,
            },
        ]
    )


def test_recommendation_floor_matches_live_repair_policy():
    df = _score_rows()

    default_picks = select_daily_candidates(df, score_col="score", prob_col="hybrid_mean")
    repaired_picks = select_daily_candidates(
        df,
        score_col="score",
        prob_col="hybrid_mean",
        floor_bull=0.35,
        floor_bear=0.40,
        fallback_floor=0.35,
    )
    stats = daily_selection_stats(
        df,
        prob_col="hybrid_mean",
        floor_bull=0.35,
        floor_bear=0.40,
        fallback_floor=0.35,
    )

    assert default_picks.empty
    assert repaired_picks["code"].tolist() == ["000001"]
    assert stats.iloc[0]["safe_pool_count"] == 1
    assert stats.iloc[0]["floor_used"] == 0.35


def test_pickle_compat_registers_legacy_main_calibrator(monkeypatch):
    main_mod = sys.modules["__main__"]
    monkeypatch.delattr(main_mod, "PassThroughCalibrator", raising=False)

    common_v2.ensure_pickle_compat()

    assert getattr(main_mod, "PassThroughCalibrator") is common_v2.PassThroughCalibrator


def test_scanner_classifies_selected_rows_using_hybrid_mean_as_probability():
    row = pd.Series(
        {
            "selection_mode": "SELECTED",
            "hybrid_mean": 0.36,
            "meta_score": -0.03,
            "score": -0.03,
        }
    )

    classified = classify_v2_csv_pick(row)

    assert classified["should_save"] is True
    assert classified["position_tag"] == "META_V2"
    assert classified["pick_type"] == "MAIN"
    assert classified["prob"] == 0.36
    assert classified["meta_score"] == -0.03


def test_scanner_skips_fallback_diagnostic_rows():
    classified = classify_v2_csv_pick(
        pd.Series({"selection_mode": "FALLBACK_DIAGNOSTIC", "hybrid_mean": 0.20, "score": 0.99})
    )

    assert classified["should_save"] is False
    assert classified["position_tag"] == "EMPTY"


def test_swing_funnel_report_separates_raw_and_unique_event_counts():
    events = [
        {
            "stage": "blocked_swing_gap",
            "stock_code": "000001",
            "stock_name": "A",
            "record_id": 1,
            "fields": {"strategy": "KOSPI_ML"},
        },
        {
            "stage": "blocked_swing_gap",
            "stock_code": "000001",
            "stock_name": "A",
            "record_id": 1,
            "fields": {"strategy": "KOSPI_ML"},
        },
        {
            "stage": "blocked_gatekeeper_reject",
            "stock_code": "000002",
            "stock_name": "B",
            "record_id": 2,
            "fields": {"strategy": "KOSPI_ML", "action": "눌림 대기"},
        },
        {
            "stage": "order_bundle_submitted",
            "stock_code": "000003",
            "stock_name": "C",
            "record_id": 3,
            "fields": {"strategy": "KOSPI_ML"},
        },
        {
            "stage": "swing_sim_order_bundle_assumed_filled",
            "stock_code": "000004",
            "stock_name": "D",
            "record_id": 4,
            "fields": {
                "strategy": "KOSPI_ML",
                "actual_order_submitted": False,
            },
        },
    ]

    summary = summarize_pipeline_events(events)

    assert summary["raw_counts"]["blocked_swing_gap"] == 2
    assert summary["unique_record_counts"]["blocked_swing_gap"] == 1
    assert summary["gatekeeper_actions"]["눌림 대기"] == 1
    assert summary["submitted_unique_records"] == 1
    assert summary["simulated_order_unique_records"] == 1


def test_build_swing_selection_funnel_report_from_injected_sources():
    report = build_swing_selection_funnel_report(
        "2026-05-08",
        recommendation_rows=[
            {
                "selection_mode": "SELECTED",
                "position_tag": "META_V2",
                "hybrid_mean": 0.36,
                "meta_score": 0.01,
            }
        ],
        diagnostic_summary={
            "owner": "SwingModelSelectionFunnelRepair",
            "selection_mode": "SELECTED",
            "selected_count": 1,
            "fallback_written_to_recommendations": False,
        },
        db_rows=[
            {
                "position_tag": "META_V2",
                "status": "WATCHING",
                "buy_qty": 0,
                "buy_time": None,
            }
        ],
        event_rows=[],
    )

    assert report["model_selection"]["selected_count"] == 1
    assert report["recommendation_csv"]["selection_modes"]["SELECTED"] == 1
    assert report["db_recommendations"]["by_position_status"]["META_V2:WATCHING"] == 1
    json.dumps(report, ensure_ascii=False)


def test_swing_daily_simulation_skips_fallback_diagnostics():
    recs = pd.DataFrame(
        [
            {"date": "2026-05-08", "code": "000001", "selection_mode": "SELECTED"},
            {"date": "2026-05-08", "code": "000002", "selection_mode": "FALLBACK_DIAGNOSTIC"},
        ]
    )

    live, summary = filter_live_recommendations(recs)

    assert live["code"].tolist() == ["000001"]
    assert summary["diagnostic_rows"] == 1


def test_swing_daily_simulation_closes_tp_path():
    recs = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-05-08"),
                "code": "000001",
                "name": "A",
                "selection_mode": "SELECTED",
                "bull_regime": 1,
                "hybrid_mean": 0.36,
                "meta_score": 0.1,
                "score_rank": 1,
                "floor_used": 0.35,
                "close": 100.0,
            }
        ]
    )
    quotes = pd.DataFrame(
        [
            {
                "quote_date": pd.Timestamp("2026-05-11"),
                "stock_code": "000001",
                "open_price": 100.0,
                "high_price": 106.0,
                "low_price": 99.0,
                "close_price": 105.0,
            }
        ]
    )

    rows = simulate_swing_recommendations(recs, quotes, target_date="2026-05-11")

    assert rows[0]["status"] == "CLOSED_SIM"
    assert rows[0]["entry_guard"] == "PASS_DRY_RUN"
    assert rows[0]["actual_order_submitted"] is False
    assert rows[0]["order_type_code"] == "6"
    assert rows[0]["exit_reason"] == "PRESET_TARGET"
    assert round(rows[0]["net_ret"], 4) == 0.0477


def test_build_swing_daily_simulation_report_from_injected_sources():
    report = build_swing_daily_simulation_report(
        "2026-05-08",
        recommendation_rows=pd.DataFrame(
            [{"date": "2026-05-08", "code": "000001", "selection_mode": "SELECTED"}]
        ),
        quote_rows=pd.DataFrame(),
    )

    assert report["report_type"] == "swing_daily_simulation"
    assert report["recommendation_summary"]["live_rows"] == 1
    assert report["simulation_summary"]["status_counts"]["PENDING_ENTRY"] == 1


def test_swing_lifecycle_audit_tracks_full_funnel_and_observation_axes():
    report = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[
            {
                "selection_mode": "SELECTED",
                "position_tag": "META_V2",
                "hybrid_mean": 0.36,
                "meta_score": 0.01,
            }
        ],
        diagnostic_summary={
            "owner": "SwingModelSelectionFunnelRepair",
            "selection_mode": "SELECTED",
            "selected_count": 1,
            "floor_bull": 0.35,
            "floor_bear": 0.40,
            "safe_pool_count": 1,
            "fallback_written_to_recommendations": False,
        },
        db_rows=[
            {
                "position_tag": "META_V2",
                "status": "COMPLETED",
                "buy_qty": 1,
                "buy_time": "2026-05-08T09:30:00",
                "profit_rate": 1.2,
                "profit": 1200,
            }
        ],
        event_rows=[
            {
                "stage": "blocked_swing_gap",
                "stock_code": "000001",
                "stock_name": "A",
                "record_id": 1,
                "fields": {"strategy": "KOSPI_ML", "gap_pct": 3.2},
            },
            {
                "stage": "blocked_gatekeeper_reject",
                "stock_code": "000002",
                "stock_name": "B",
                "record_id": 2,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "action": "눌림 대기",
                    "cooldown_sec": 1200,
                    "gatekeeper_eval_ms": 1000,
                },
            },
            {
                "stage": "swing_sim_scale_in_order_assumed_filled",
                "stock_code": "000003",
                "stock_name": "C",
                "record_id": 3,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "add_type": "PYRAMID",
                    "effective_qty": 2,
                    "actual_order_submitted": False,
                },
            },
            {
                "stage": "swing_sim_sell_order_assumed_filled",
                "stock_code": "000003",
                "stock_name": "C",
                "record_id": 3,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "exit_source": "PRESET_TARGET",
                    "profit_rate": 1.5,
                    "actual_order_submitted": False,
                },
            },
        ],
    )

    assert report["report_type"] == "swing_lifecycle_audit"
    assert report["lifecycle_events"]["unique_record_counts"]["blocked_swing_gap"] == 1
    assert report["lifecycle_events"]["gatekeeper_actions"]["눌림 대기"] == 1
    assert report["lifecycle_events"]["add_types"]["PYRAMID"] == 1
    assert report["db_lifecycle"]["completed_rows"] == 1
    axis_status = {axis["axis_id"]: axis["status"] for axis in report["observation_axes"]}
    assert axis_status["swing_scale_in_avg_down_pyramid"] == "ready"
    json.dumps(report, ensure_ascii=False)


def test_swing_threshold_ai_review_is_proposal_only_and_guarded():
    audit = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[],
        diagnostic_summary={"selected_count": 0},
        db_rows=[],
        event_rows=[],
    )
    raw_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "swing_model_floor",
                "anomaly_type": "entry_drought",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "adjust_down",
                    "proposed_value": 0.1,
                    "anomaly_route": "threshold_candidate",
                    "sample_window": "rolling_5d",
                },
                "correction_reason": "candidate count is empty",
                "required_evidence": ["safe_pool_count"],
                "risk_flags": ["sample_shortage"],
            }
        ],
    }

    review = build_swing_threshold_ai_review_report(audit, ai_raw_response=raw_response)
    item = next(row for row in review["items"] if row["family"] == "swing_model_floor")

    assert review["runtime_change"] is False
    assert review["policy"]["authority"] == "proposal_only"
    assert item["guard_decision"]["effective_value"] == 0.2
    assert item["guard_decision"]["clamped"] is True
    assert item["guard_decision"]["runtime_change"] is False


def test_swing_improvement_automation_emits_workorder_ready_orders():
    audit = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[{"selection_mode": "SELECTED", "position_tag": "META_V2"}],
        diagnostic_summary={"selected_count": 1},
        db_rows=[],
        event_rows=[
            {
                "stage": "blocked_gatekeeper_reject",
                "stock_code": "000002",
                "stock_name": "B",
                "record_id": 2,
                "fields": {"strategy": "KOSPI_ML", "action": "전량 회피"},
            }
        ],
    )
    automation = build_swing_improvement_automation_report(audit)
    orders = {order["order_id"]: order for order in automation["code_improvement_orders"]}

    assert automation["report_type"] == "swing_improvement_automation"
    assert orders["order_swing_gatekeeper_reject_threshold_review"]["lifecycle_stage"] == "entry"
    assert orders["order_swing_ai_contract_structured_output_eval"]["runtime_effect"] is False
    assert automation["auto_family_candidates"]


def test_write_swing_lifecycle_outputs_creates_all_artifacts(tmp_path):
    outputs = write_swing_lifecycle_outputs(
        "2026-05-08",
        output_root=tmp_path,
        ai_review_provider="none",
        recommendation_rows=[],
        diagnostic_summary={"selected_count": 0},
        db_rows=[],
        event_rows=[],
    )

    for path in outputs["paths"].values():
        assert tmp_path in Path(path).parents
        assert Path(path).exists()
