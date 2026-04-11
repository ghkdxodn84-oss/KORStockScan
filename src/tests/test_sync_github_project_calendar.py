from src.engine.sync_github_project_calendar import _event_body, _parse_project_item, ProjectItem


def _sample_node():
    return {
        "id": "PVTI_xxx",
        "isArchived": False,
        "content": {
            "__typename": "Issue",
            "title": "Implement remote fetch hardening",
            "url": "https://github.com/org/repo/issues/123",
            "state": "OPEN",
            "assignees": {"nodes": [{"login": "alice"}, {"login": "bob"}]},
        },
        "fieldValues": {
            "nodes": [
                {
                    "__typename": "ProjectV2ItemFieldDateValue",
                    "date": "2026-04-13",
                    "field": {"name": "Due"},
                },
                {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "name": "In Progress",
                    "field": {"name": "Status"},
                },
                {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "name": "Scalping Logic",
                    "field": {"name": "Track"},
                },
            ]
        },
    }


def test_parse_project_item_returns_item_when_due_exists():
    parsed = _parse_project_item(
        _sample_node(),
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
    )
    assert parsed is not None
    assert parsed.item_id == "PVTI_xxx"
    assert parsed.title == "Implement remote fetch hardening"
    assert parsed.due_date == "2026-04-13"
    assert parsed.status == "In Progress"
    assert parsed.track == "Scalping Logic"
    assert parsed.assignees == "alice, bob"


def test_parse_project_item_returns_none_when_due_missing():
    node = _sample_node()
    node["fieldValues"]["nodes"] = [fv for fv in node["fieldValues"]["nodes"] if fv.get("__typename") != "ProjectV2ItemFieldDateValue"]
    parsed = _parse_project_item(
        node,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
    )
    assert parsed is None


def test_event_body_contains_private_extended_properties():
    item = ProjectItem(
        item_id="PVTI_1",
        content_type="Issue",
        title="Task A",
        url="https://github.com/org/repo/issues/1",
        due_date="2026-04-14",
        status="Todo",
        track="Prompt",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(item, event_prefix="[KORStockScan]", owner="org", project_number=3)
    assert body["summary"] == "[KORStockScan] Task A"
    assert body["start"]["date"] == "2026-04-14"
    assert body["end"]["date"] == "2026-04-15"
    assert body["extendedProperties"]["private"]["gh_project_item_id"] == "PVTI_1"
