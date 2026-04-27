from src.engine.build_codex_daily_workorder import (
    ProjectTask,
    _filter_stale_same_day_managed_tasks,
    _parse_project_item,
    _matches_slot,
    _resolve_slot_filters_for_target_date,
    _split_csv,
    render_markdown,
    sort_tasks,
)


def test_split_csv_trims_and_drops_empty():
    assert _split_csv("Todo, In Progress, ,Done") == ["Todo", "In Progress", "Done"]


def test_sort_tasks_by_status_due_track_title():
    tasks = [
        ProjectTask(
            item_id="3",
            content_type="DraftIssue",
            title="B task",
            url="",
            due_date="2026-04-15",
            status="Todo",
            track="Plan",
            slot="PREOPEN",
            time_window="08:20~08:50",
            assignees="",
            state="",
            source="docs/plan.md",
            section="아직 남아있는 일",
        ),
        ProjectTask(
            item_id="2",
            content_type="DraftIssue",
            title="A task",
            url="",
            due_date="2026-04-14",
            status="In Progress",
            track="AIPrompt",
            slot="INTRADAY",
            time_window="10:00~10:30",
            assignees="",
            state="",
            source="docs/prompt.md",
            section="P0. 즉시 착수 가능한 확인/계측",
        ),
        ProjectTask(
            item_id="1",
            content_type="DraftIssue",
            title="C task",
            url="",
            due_date="2026-04-14",
            status="Todo",
            track="Checklist0414",
            slot="POSTCLOSE",
            time_window="15:40~16:10",
            assignees="",
            state="",
            source="docs/checklist.md",
            section="체크박스 미완료",
        ),
    ]
    sorted_tasks = sort_tasks(tasks, ["In Progress", "Todo"])
    assert [t.item_id for t in sorted_tasks] == ["2", "1", "3"]


def test_render_markdown_includes_template_and_ids():
    tasks = [
        ProjectTask(
            item_id="ITEM_123",
            content_type="Issue",
            title="테스트 작업",
            url="https://example.com/issue/1",
            due_date="2026-04-13",
            status="Todo",
            track="Plan",
            slot="PREOPEN",
            time_window="08:20~08:50",
            assignees="jaehwan",
            state="OPEN",
            source="docs/example.md",
            section="P0. 즉시 착수 가능한 확인/계측",
            apply_target="remote",
        )
    ]
    md = render_markdown(
        owner="JaehwanPark",
        project_number=1,
        project_title="KORStockScan Ops",
        generated_at="2026-04-11T23:00:00+09:00",
        target_date="2026-04-12",
        include_overdue=True,
        holiday_override=True,
        holiday_reason="weekend",
        statuses=["Todo", "In Progress"],
        slots=["PREOPEN"],
        tasks=tasks,
        max_items=20,
    )
    assert "Codex 일일 작업지시서" in md
    assert "ITEM_123" in md
    assert "Codex 전달 템플릿" in md
    assert "슬롯필터" in md
    assert "docs/example.md" in md
    assert "기준일자" in md
    assert "휴장일 재분류" in md
    assert "반영대상" in md
    removed_rule = "현재 시간 기준으로" + " 작업시작 시간이 도래한 작업만 실행"
    assert removed_rule not in md
    assert "작업시간이 지났으나 반복적으로 실행해야하는 작업" in md


def test_matches_slot_case_insensitive():
    assert _matches_slot("PREOPEN", {"preopen"})
    assert not _matches_slot("INTRADAY", {"preopen"})
    assert _matches_slot("", set())


def test_resolve_slot_filters_promotes_intraday_on_holiday():
    slots, holiday_override, reason = _resolve_slot_filters_for_target_date(
        selected_slots=["INTRADAY"],
        target_date="2026-04-12",
    )
    assert slots == []
    assert holiday_override is True
    assert reason == "weekend"


def test_resolve_slot_filters_skips_preopen_on_holiday():
    slots, holiday_override, reason = _resolve_slot_filters_for_target_date(
        selected_slots=["PREOPEN"],
        target_date="2026-04-12",
    )
    assert slots == ["__holiday_skip__"]
    assert holiday_override is True
    assert reason == "weekend"


def test_parse_project_item_defaults_apply_target_without_postprocessing():
    node = {
        "id": "PVTI_plain",
        "isArchived": False,
        "content": {
            "__typename": "DraftIssue",
            "title": "장중 canary 모니터링",
            "url": "",
            "body": "Source: `docs/checklist.md`\nSection: `원격 canary 후보 검토`",
            "state": "OPEN",
            "assignees": {"nodes": []},
        },
        "fieldValues": {
            "nodes": [
                {
                    "__typename": "ProjectV2ItemFieldDateValue",
                    "date": "2026-04-23",
                    "field": {"name": "Due"},
                },
                {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "name": "Todo",
                    "field": {"name": "Status"},
                },
            ]
        },
    }

    parsed = _parse_project_item(
        node,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
    )

    assert parsed is not None
    assert parsed.apply_target == "-"


def test_filter_stale_same_day_managed_tasks_uses_docs_as_source_of_truth(monkeypatch):
    live_task = ProjectTask(
        item_id="1",
        content_type="DraftIssue",
        title="[Checklist0427] [LatencyCanary0427-2] other_danger-only residual override 13:00 즉시 재점검",
        url="",
        due_date="2026-04-27",
        status="Todo",
        track="Checklist0427",
        slot="INTRADAY",
        time_window="13:00~13:20",
        assignees="",
        state="OPEN",
        source="docs/2026-04-27-stage2-todo-checklist.md",
        section="체크박스 미완료",
    )
    stale_task = ProjectTask(
        item_id="2",
        content_type="DraftIssue",
        title="[Checklist0427] [LatencyOps0427] gatekeeper_fast_reuse signature/window 독립축 PREOPEN 승인 판정",
        url="",
        due_date="2026-04-27",
        status="Todo",
        track="Checklist0427",
        slot="PREOPEN",
        time_window="08:20~08:35",
        assignees="",
        state="OPEN",
        source="docs/2026-04-27-stage2-todo-checklist.md",
        section="체크박스 미완료",
    )
    foreign_task = ProjectTask(
        item_id="3",
        content_type="DraftIssue",
        title="외부 수동 항목",
        url="",
        due_date="2026-04-27",
        status="Todo",
        track="Plan",
        slot="INTRADAY",
        time_window="10:00~10:30",
        assignees="",
        state="OPEN",
        source="manual",
        section="manual",
    )

    class DummyTask:
        def __init__(self, title: str, due_date: str, track: str):
            self.title = title
            self.due_date = due_date
            self.track = track

    monkeypatch.setattr(
        "src.engine.build_codex_daily_workorder.collect_backlog_tasks",
        lambda: [DummyTask("[LatencyCanary0427-2] other_danger-only residual override 13:00 즉시 재점검", "2026-04-27", "Checklist0427")],
    )

    filtered = _filter_stale_same_day_managed_tasks(
        [live_task, stale_task, foreign_task],
        "2026-04-27",
    )
    assert [task.item_id for task in filtered] == ["1", "3"]
