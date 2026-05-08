import json

from src.engine import threshold_cycle_ev_report as mod


def test_build_threshold_cycle_ev_report_uses_existing_reports(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monitor_dir = report_dir / "monitor_snapshots"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    apply_dir = tmp_path / "apply_plans"
    ev_dir = report_dir / "threshold_cycle_ev"
    automation_dir = report_dir / "scalping_pattern_lab_automation"
    monitor_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    apply_dir.mkdir(parents=True)
    automation_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "apply_manifest_path", lambda target_date: apply_dir / f"threshold_apply_{target_date}.json")
    monkeypatch.setattr(
        mod,
        "automation_report_paths",
        lambda target_date: (
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.json",
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.md",
        ),
    )

    (monitor_dir / "trade_review_2026-05-08.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "completed_trades": 2,
                    "open_trades": 0,
                    "win_trades": 1,
                    "loss_trades": 1,
                    "avg_profit_rate": -0.39,
                    "realized_pnl_krw": -282,
                }
            }
        ),
        encoding="utf-8",
    )
    (monitor_dir / "performance_tuning_2026-05-08.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "budget_pass_events": 100,
                    "order_bundle_submitted_events": 5,
                    "latency_block_events": 95,
                    "latency_pass_events": 5,
                    "full_fill_events": 2,
                    "partial_fill_events": 0,
                    "full_fill_completed_avg_profit_rate": -0.395,
                    "holding_reviews": 17,
                    "exit_signals": 2,
                    "holding_review_ms_p95": 17022,
                }
            }
        ),
        encoding="utf-8",
    )
    (calibration_dir / "threshold_cycle_calibration_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "run_phase": "postclose",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "calibration_state": "adjust_up",
                        "sample_count": 20,
                        "sample_floor": 20,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (apply_dir / "threshold_apply_2026-05-08.json").write_text(
        json.dumps(
            {
                "status": "auto_bounded_live_ready",
                "runtime_change": True,
                "auto_apply_selected": [{"family": "score65_74_recovery_probe"}],
            }
        ),
        encoding="utf-8",
    )
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "ev_report_summary": {
                    "gemini_fresh": True,
                    "claude_fresh": True,
                    "consensus_count": 1,
                    "auto_family_candidate_count": 0,
                    "code_improvement_order_count": 1,
                    "top_consensus_findings": [
                        {
                            "title": "AI threshold miss EV 회수 조건 점검",
                            "route": "existing_family",
                            "mapped_family": "score65_74_recovery_probe",
                        }
                    ],
                    "top_code_improvement_orders": [
                        {
                            "order_id": "order_ai_threshold",
                            "title": "AI threshold miss EV 회수 조건 점검",
                            "target_subsystem": "entry_funnel",
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_threshold_cycle_ev_report("2026-05-08")

    assert report["runtime_apply"]["selected_families"] == ["score65_74_recovery_probe"]
    assert report["daily_ev_summary"]["completed_trades"] == 2
    assert report["daily_ev_summary"]["realized_pnl_krw"] == -282
    assert report["entry_funnel"]["budget_pass_to_submitted_rate_pct"] == 5.0
    assert report["pattern_lab_automation"]["consensus_count"] == 1
    assert report["pattern_lab_automation"]["top_consensus_findings"][0]["mapped_family"] == "score65_74_recovery_probe"
    assert (ev_dir / "threshold_cycle_ev_2026-05-08.json").exists()
    assert (ev_dir / "threshold_cycle_ev_2026-05-08.md").exists()


def test_build_threshold_cycle_ev_report_warns_when_pattern_lab_artifact_missing(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monitor_dir = report_dir / "monitor_snapshots"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    apply_dir = tmp_path / "apply_plans"
    ev_dir = report_dir / "threshold_cycle_ev"
    automation_dir = report_dir / "scalping_pattern_lab_automation"
    monitor_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    apply_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "apply_manifest_path", lambda target_date: apply_dir / f"threshold_apply_{target_date}.json")
    monkeypatch.setattr(
        mod,
        "automation_report_paths",
        lambda target_date: (
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.json",
            automation_dir / f"scalping_pattern_lab_automation_{target_date}.md",
        ),
    )

    (monitor_dir / "trade_review_2026-05-08.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (monitor_dir / "performance_tuning_2026-05-08.json").write_text(json.dumps({"metrics": {}}), encoding="utf-8")
    (calibration_dir / "threshold_cycle_calibration_2026-05-08_postclose.json").write_text(
        json.dumps({"run_phase": "postclose"}),
        encoding="utf-8",
    )
    (apply_dir / "threshold_apply_2026-05-08.json").write_text(json.dumps({"status": "manifest_ready"}), encoding="utf-8")

    report = mod.build_threshold_cycle_ev_report("2026-05-08")

    assert report["pattern_lab_automation"]["available"] is False
    assert "pattern_lab_automation_missing" in report["warnings"]
    markdown = (ev_dir / "threshold_cycle_ev_2026-05-08.md").read_text(encoding="utf-8")
    assert "AI threshold miss EV 회수 조건 점검" not in markdown
