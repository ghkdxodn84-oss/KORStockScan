from src.engine import sniper_entry_pipeline_report as report_mod


def test_latest_attempt_events_excludes_previous_submitted_attempt(monkeypatch):
    lines = [
        "[2026-04-07 09:00:00] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=ai_confirmed id=11",
        "[2026-04-07 09:00:01] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=entry_armed id=11",
        "[2026-04-07 09:00:02] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=budget_pass id=11",
        "[2026-04-07 09:00:03] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=latency_pass id=11",
        "[2026-04-07 09:00:04] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=order_bundle_submitted id=11",
        "[2026-04-07 10:00:00] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=ai_confirmed id=11",
        "[2026-04-07 10:00:01] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=entry_armed id=11",
        "[2026-04-07 10:00:02] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=budget_pass id=11",
        "[2026-04-07 10:00:03] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=latency_block id=11 reason=latency_state_danger",
    ]
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda log_path, *, target_date: lines)

    report = report_mod.build_entry_pipeline_flow_report("2026-04-07")

    row = report["sections"]["recent_stocks"][0]
    assert [item["stage"] for item in row["pass_flow"]] == [
        "watching",
        "ai_confirmed",
        "entry_armed",
        "budget_pass",
    ]
    assert row["confirmed_failure"]["stage"] == "latency_block"
    assert row["record_id"] == "11"
    assert all(event["stage"] != "order_bundle_submitted" for event in row["events"])


def test_latest_attempt_prefers_new_record_id_for_same_stock(monkeypatch):
    lines = [
        "[2026-04-07 09:00:00] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=ai_confirmed id=11",
        "[2026-04-07 09:00:01] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=entry_armed id=11",
        "[2026-04-07 09:00:02] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=order_bundle_submitted id=11",
        "[2026-04-07 09:00:03] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=dual_persona_shadow id=11 decision_type=gatekeeper",
        "[2026-04-07 10:00:00] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=ai_confirmed id=12",
        "[2026-04-07 10:00:01] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=entry_armed id=12",
        "[2026-04-07 10:00:02] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=blocked_zero_qty id=12 qty=0",
    ]
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda log_path, *, target_date: lines)

    report = report_mod.build_entry_pipeline_flow_report("2026-04-07")

    row = report["sections"]["recent_stocks"][0]
    assert row["record_id"] == "12"
    assert row["latest_status"]["stage"] == "blocked_zero_qty"
    assert [item["stage"] for item in row["pass_flow"]] == [
        "watching",
        "ai_confirmed",
        "entry_armed",
    ]
    assert all(event["fields"].get("id") == "12" for event in row["events"])
