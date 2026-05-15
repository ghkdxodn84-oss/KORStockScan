import json
from pathlib import Path

from src.engine import build_next_stage2_checklist as mod
from src.engine.sync_docs_backlog_to_project import parse_checklist_tasks


def _patch_dirs(monkeypatch, tmp_path):
    docs = tmp_path / "docs"
    ev = tmp_path / "data" / "report" / "threshold_cycle_ev"
    openai = tmp_path / "data" / "report" / "openai_ws"
    swing = tmp_path / "data" / "report" / "swing_runtime_approval"
    code = tmp_path / "data" / "report" / "code_improvement_workorder"
    for path in (docs, ev, openai, swing, code):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "DOCS_DIR", docs)
    monkeypatch.setattr(mod, "CHECKLIST_DIR", docs / "checklists")
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev)
    monkeypatch.setattr(mod, "OPENAI_WS_REPORT_DIR", openai)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_REPORT_DIR", code)
    return docs, ev, openai, swing, code


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_next_stage2_checklist_generates_next_trading_day_and_tasks(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-08.json",
        {
            "runtime_apply": {
                "runtime_change": True,
                "selected_families": ["score65_74_recovery_probe"],
            },
            "scalp_simulator": {"event_count": 3},
            "code_improvement_workorder": {"selected_order_count": 2},
        },
    )
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-08.json",
        {
            "decision": "keep_ws",
            "entry_price_canary_summary": {
                "canary_event_count": 2,
                "transport_observable_count": 0,
                "instrumentation_gap": True,
            },
        },
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-08.json", {"approval_requests": [{"id": "req"}]})
    _write_json(code_dir / "code_improvement_workorder_2026-05-08.json", {"summary": {"selected_order_count": 2}})

    summary = mod.build_next_stage2_checklist("2026-05-08")

    assert summary["target_date"] == "2026-05-11"
    checklist = docs / "checklists" / "2026-05-11-stage2-todo-checklist.md"
    text = checklist.read_text(encoding="utf-8")
    assert "[ThresholdEnvAutoApplyPreopen0511]" in text
    assert "[SwingApprovalArtifactPreopen0511]" in text
    assert "[RuntimeEnvIntradayObserve0511]" in text
    assert "[OpenAIWSIntradaySample0511]" in text
    assert "[SimProbeIntradayCoverage0511]" in text
    assert "[CodeImprovementWorkorderReview0511]" in text
    assert "codex_daily_workorder_*.md" in text


def test_build_next_stage2_checklist_preserves_manual_content_and_replaces_auto_block(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-11.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(openai_dir / "openai_ws_stability_2026-05-11.json", {"decision": "keep_ws"})
    _write_json(swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-11.json", {"summary": {"selected_order_count": 0}})
    target = docs / "checklists" / "2026-05-12-stage2-todo-checklist.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            [
                "# 2026-05-12 Stage2 To-Do Checklist",
                "",
                "- [ ] `[ThresholdEnvAutoApplyPreopen0512] 수동 장전 항목` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)",
                "",
                "manual-only-line",
                "",
                "## Project/Calendar 동기화",
                "",
                "manual-sync-line",
            ]
        ),
        encoding="utf-8",
    )

    mod.build_next_stage2_checklist("2026-05-11")
    mod.build_next_stage2_checklist("2026-05-11")

    text = target.read_text(encoding="utf-8")
    assert "manual-only-line" in text
    assert "manual-sync-line" in text
    assert text.count("ThresholdEnvAutoApplyPreopen0512") == 1
    assert text.count(mod.AUTO_START) == 1
    assert text.count(mod.AUTO_END) == 1


def test_build_next_stage2_checklist_excludes_codex_daily_workorder_snapshots(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    (docs / "code-improvement-workorders").mkdir(parents=True, exist_ok=True)
    (docs / "code-improvement-workorders" / "codex_daily_workorder_2026-05-11_PREOPEN.md").write_text(
        "FakeCodexOnlyFamily",
        encoding="utf-8",
    )
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-11.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-11.json",
        {"decision": "keep_ws", "entry_price_canary_summary": {"canary_event_count": 0}},
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-11.json", {"summary": {"selected_order_count": 0}})

    mod.build_next_stage2_checklist("2026-05-11")

    text = (docs / "checklists" / "2026-05-12-stage2-todo-checklist.md").read_text(encoding="utf-8")
    assert "FakeCodexOnlyFamily" not in text
    assert "RuntimeEnvIntradayObserve0512" not in text


def test_generated_checklist_is_parser_friendly(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-11.json", {"runtime_apply": {"runtime_change": True}})
    _write_json(openai_dir / "openai_ws_stability_2026-05-11.json", {"decision": "rollback_http"})
    _write_json(swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-11.json", {"summary": {"selected_order_count": 1}})

    mod.build_next_stage2_checklist("2026-05-11")
    checklist = docs / "checklists" / "2026-05-12-stage2-todo-checklist.md"
    monkeypatch.setenv("DOC_BACKLOG_TODAY", "2026-05-11")
    monkeypatch.setenv("DOC_CHECKLIST_PATH", str(checklist))

    tasks = [task for task in parse_checklist_tasks() if task.source == str(checklist)]
    titles = [task.title for task in tasks]

    assert any("ThresholdEnvAutoApplyPreopen0512" in title for title in titles)
    assert any("RuntimeEnvIntradayObserve0512" in title for title in titles)
    assert all(task.due_date == "2026-05-12" for task in tasks)
