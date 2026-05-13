import json

from src.engine import plan_rebase_daily_renewal as mod


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_plan_rebase_daily_renewal_builds_proposal_only_artifact(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    runtime_dir = tmp_path / "runtime_approval_summary"
    openai_dir = tmp_path / "openai_ws"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "plan_rebase_daily_renewal"
    plan = tmp_path / "docs" / "plan.md"
    prompt = tmp_path / "docs" / "prompt.md"
    agents = tmp_path / "AGENTS.md"
    for path in (plan, prompt, agents):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("existing", encoding="utf-8")

    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "RUNTIME_APPROVAL_SUMMARY_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPENAI_WS_REPORT_DIR", openai_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "PLAN_REBASE_RENEWAL_DIR", out_dir)
    monkeypatch.setattr(mod, "PLAN_REBASE_PATH", plan)
    monkeypatch.setattr(mod, "PROMPT_PATH", prompt)
    monkeypatch.setattr(mod, "AGENTS_PATH", agents)

    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-13.json",
        {
            "runtime_apply": {
                "runtime_change": True,
                "selected_families": ["soft_stop_whipsaw_confirmation", "score65_74_recovery_probe"],
                "runtime_env_file": "data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-13.env",
            }
        },
    )
    _write_json(
        runtime_dir / "runtime_approval_summary_2026-05-13.json",
        {
            "summary": {
                "swing_requested": 2,
                "swing_approved": 0,
                "panic_approval_requested": 1,
            },
            "scalping": [
                {"family": "soft_stop_whipsaw_confirmation", "selected_auto_bounded_live": True},
                {"family": "position_sizing_cap_release", "selected_auto_bounded_live": False, "state": "hold_sample"},
            ],
            "panic": [{"family": "panic_entry_freeze_guard", "state": "approval_required"}],
            "warnings": [],
        },
    )
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-13.json",
        {
            "decision": "keep_ws",
            "entry_price_canary_summary": {
                "canary_event_count": 3,
                "transport_observable_count": 3,
                "instrumentation_gap": False,
            },
        },
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-13.json", {"summary": {"requested": 2, "approved": 0}})

    report = mod.build_plan_rebase_daily_renewal("2026-05-13")

    assert report["mode"] == "proposal_only"
    assert report["runtime_mutation_allowed"] is False
    assert report["document_mutation_allowed"] is False
    assert report["renewal_state"] == "proposal_ready"
    assert report["proposal"]["plan_rebase"]["current_runtime_apply"]["selected_families"] == [
        "soft_stop_whipsaw_confirmation",
        "score65_74_recovery_probe",
    ]
    assert report["proposal"]["plan_rebase"]["open_state_summary"]["swing"]["approval_artifact_required"] is True
    assert "metric_decision_contract" in report["guardrails"]["forbidden_update_scope"]
    markdown = (out_dir / "plan_rebase_daily_renewal_2026-05-13.md").read_text(encoding="utf-8")
    assert "proposal_only" in markdown
    assert "soft_stop_whipsaw_confirmation" in markdown
    assert plan.read_text(encoding="utf-8") == "existing"
    assert prompt.read_text(encoding="utf-8") == "existing"
    assert agents.read_text(encoding="utf-8") == "existing"


def test_plan_rebase_daily_renewal_blocks_when_required_sources_missing(tmp_path, monkeypatch):
    out_dir = tmp_path / "plan_rebase_daily_renewal"
    monkeypatch.setattr(mod, "EV_REPORT_DIR", tmp_path / "missing_ev")
    monkeypatch.setattr(mod, "RUNTIME_APPROVAL_SUMMARY_DIR", tmp_path / "missing_runtime")
    monkeypatch.setattr(mod, "OPENAI_WS_REPORT_DIR", tmp_path / "missing_openai")
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", tmp_path / "missing_swing")
    monkeypatch.setattr(mod, "PLAN_REBASE_RENEWAL_DIR", out_dir)
    monkeypatch.setattr(mod, "PLAN_REBASE_PATH", tmp_path / "missing_plan.md")
    monkeypatch.setattr(mod, "PROMPT_PATH", tmp_path / "missing_prompt.md")
    monkeypatch.setattr(mod, "AGENTS_PATH", tmp_path / "missing_agents.md")

    report = mod.build_plan_rebase_daily_renewal("2026-05-13")

    assert report["renewal_state"] == "blocked_missing_or_warning_sources"
    assert "threshold_cycle_ev_missing" in report["warnings"]
    assert "runtime_approval_summary_missing" in report["warnings"]
    assert report["document_mutation_allowed"] is False
