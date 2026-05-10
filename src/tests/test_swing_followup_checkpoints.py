from __future__ import annotations

from pathlib import Path

from src.engine.sync_docs_backlog_to_project import parse_checklist_tasks


def test_swing_followup_decision_checkpoints_are_parser_friendly():
    checklist = Path("docs/2026-05-11-stage2-todo-checklist.md").read_text(encoding="utf-8")

    expected = {
        "SwingRealOrderTransitionDecision0511": ("2026-05-11", "POSTCLOSE", "18:30~18:45", "ScalpingLogic"),
        "SwingNumericFloorAutoChangeDecision0511": ("2026-05-11", "POSTCLOSE", "18:45~19:00", "ScalpingLogic"),
        "ThresholdEnvAutoApplyPreopen0512": ("2026-05-12", "PREOPEN", "08:50~09:00", "RuntimeStability"),
    }

    for task_id, (due, slot, time_window, track) in expected.items():
        marker = (
            f"- [ ] `[{task_id}]"
            f""
        )
        assert marker in checklist
        assert f"`Due: {due}`" in checklist
        assert f"`Slot: {slot}`" in checklist
        assert f"`TimeWindow: {time_window}`" in checklist
        assert f"`Track: {track}`" in checklist


def test_checklist_parser_uses_item_due_when_it_differs_from_file_date(tmp_path, monkeypatch):
    checklist = tmp_path / "2026-05-11-stage2-todo-checklist.md"
    checklist.write_text(
        "\n".join(
            [
                "# checklist",
                "## 장전 체크리스트",
                "- [ ] `[ThresholdEnvAutoApplyPreopen0512] threshold env 자동 apply 다음 장전 확인` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DOC_CHECKLIST_PATH", str(checklist))
    monkeypatch.setenv("DOC_BACKLOG_TODAY", "2026-05-10")

    parsed = [task for task in parse_checklist_tasks() if task.source == str(checklist)]

    assert len(parsed) == 1
    assert parsed[0].due_date == "2026-05-12"
