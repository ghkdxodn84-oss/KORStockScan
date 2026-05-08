import json

from src.engine import build_code_improvement_workorder as mod


def test_build_code_improvement_workorder_classifies_and_renders(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    ev_dir.mkdir()
    payload = {
        "date": "2026-05-08",
        "ev_report_summary": {"gemini_fresh": True, "claude_fresh": True},
        "consensus_findings": [
            {
                "finding_id": "latency_guard_miss_ev_recovery",
                "title": "latency guard miss EV recovery",
                "confidence": "consensus",
                "route": "instrumentation_order",
                "mapped_family": None,
                "target_subsystem": "runtime_instrumentation",
            },
            {
                "finding_id": "ai_threshold_miss_ev_recovery",
                "title": "AI threshold miss EV recovery",
                "confidence": "consensus",
                "route": "existing_family",
                "mapped_family": "score65_74_recovery_probe",
                "target_subsystem": "entry_funnel",
            },
            {
                "finding_id": "liquidity_gate_miss_ev_recovery",
                "title": "liquidity gate miss EV recovery",
                "confidence": "consensus",
                "route": "auto_family_candidate",
                "mapped_family": None,
                "target_subsystem": "entry_filter_quality",
            },
        ],
        "solo_findings": [
            {
                "finding_id": "cache_signature_noise",
                "title": "cache signature noise",
                "confidence": "solo",
                "route": "instrumentation_order",
                "target_subsystem": "runtime_instrumentation",
            }
        ],
        "auto_family_candidates": [
            {
                "family_id": "pattern_lab_liquidity_gate_miss_ev_recovery",
                "implementation_order_id": "order_pattern_lab_liquidity_gate_miss_ev_recovery",
                "allowed_runtime_apply": False,
            }
        ],
        "code_improvement_orders": [
            {
                "order_id": "order_ai_threshold_miss_ev_recovery",
                "title": "AI threshold miss EV recovery",
                "target_subsystem": "entry_funnel",
                "priority": 2,
                "files_likely_touched": ["src/engine/daily_threshold_cycle_report.py"],
                "acceptance_tests": ["pytest threshold tests"],
                "runtime_effect": False,
            },
            {
                "order_id": "order_latency_guard_miss_ev_recovery",
                "title": "latency guard miss EV recovery",
                "target_subsystem": "runtime_instrumentation",
                "priority": 1,
                "files_likely_touched": ["src/engine/sniper_performance_tuning_report.py"],
                "acceptance_tests": ["pytest instrumentation tests"],
                "runtime_effect": False,
            },
            {
                "order_id": "order_liquidity_gate_miss_ev_recovery",
                "title": "liquidity gate miss EV recovery",
                "target_subsystem": "entry_filter_quality",
                "priority": 3,
                "files_likely_touched": ["src/engine/daily_threshold_cycle_report.py"],
                "acceptance_tests": ["pytest report tests"],
                "runtime_effect": False,
            },
            {
                "order_id": "order_cache_signature_noise",
                "title": "cache signature noise",
                "target_subsystem": "runtime_instrumentation",
                "priority": 4,
                "files_likely_touched": ["src/engine/ai_engine.py"],
                "acceptance_tests": ["pytest cache tests"],
                "runtime_effect": False,
            },
            {
                "order_id": "order_partial_fallback_shadow",
                "title": "partial fallback shadow",
                "target_subsystem": "holding_exit",
                "priority": 5,
                "files_likely_touched": ["src/engine/sniper_state_handlers.py"],
                "acceptance_tests": ["pytest holding tests"],
                "runtime_effect": False,
            },
        ],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-08.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=5)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert decisions["order_latency_guard_miss_ev_recovery"] == "implement_now"
    assert decisions["order_ai_threshold_miss_ev_recovery"] == "attach_existing_family"
    assert decisions["order_liquidity_gate_miss_ev_recovery"] == "design_family_candidate"
    assert decisions["order_cache_signature_noise"] == "defer_evidence"
    assert decisions["order_partial_fallback_shadow"] == "reject"
    assert (doc_dir / "code_improvement_workorder_2026-05-08.md").exists()
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(encoding="utf-8")
    assert "Codex 실행 지시" in markdown
    assert "order_latency_guard_miss_ev_recovery" in markdown
    assert "auto_bounded_live" in markdown


def test_build_code_improvement_workorder_limits_selected_orders(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    automation_dir.mkdir()
    payload = {
        "date": "2026-05-08",
        "consensus_findings": [],
        "solo_findings": [],
        "auto_family_candidates": [],
        "code_improvement_orders": [
            {"order_id": f"order_{idx}", "title": f"order {idx}", "priority": idx, "runtime_effect": False}
            for idx in range(5)
        ],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", tmp_path / "docs")

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=2)

    assert report["summary"]["source_order_count"] == 5
    assert report["summary"]["selected_order_count"] == 2
    assert report["deferred_or_rejected_count"] == 3
