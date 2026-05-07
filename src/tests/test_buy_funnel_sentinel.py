import json
from datetime import date

from src.engine import buy_funnel_sentinel as sentinel


def _event(
    target_date: str,
    hhmmss: str,
    stage: str,
    *,
    name: str = "테스트종목",
    code: str = "000001",
    record_id: int = 1,
    pipeline: str = "ENTRY_PIPELINE",
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "stock_name": name,
        "stock_code": code,
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{target_date}T{hhmmss}",
        "emitted_date": target_date,
    }


def _write_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    with (event_dir / f"pipeline_events_{target_date}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_previous_trading_day_skips_20260505_holiday(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        sentinel,
        "is_krx_trading_day",
        lambda target: target == date(2026, 5, 4) or target == date(2026, 5, 6),
    )
    _write_events(tmp_path, "2026-05-04", [_event("2026-05-04", "10:00:00", "ai_confirmed")])

    assert sentinel.previous_trading_day_with_events("2026-05-06") == "2026-05-04"


def test_upstream_ai_threshold_classification_uses_previous_day_baseline(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        sentinel,
        "is_krx_trading_day",
        lambda target: target == date(2026, 5, 4) or target == date(2026, 5, 6),
    )
    baseline_rows = []
    for idx in range(10):
        baseline_rows.append(_event("2026-05-04", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx))
    for idx in range(8):
        baseline_rows.append(_event("2026-05-04", f"10:{idx:02d}:10", "budget_pass", record_id=idx))
    for idx in range(4):
        baseline_rows.append(_event("2026-05-04", f"10:{idx:02d}:20", "order_bundle_submitted", record_id=idx))
    _write_events(tmp_path, "2026-05-04", baseline_rows)

    current_rows = []
    for idx in range(10):
        current_rows.append(_event("2026-05-06", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx))
    current_rows.append(_event("2026-05-06", "10:01:10", "budget_pass", record_id=1))
    current_rows.extend(
        [
            _event("2026-05-06", "10:02:00", "blocked_ai_score", record_id=20, fields={"score": "65"}),
            _event(
                "2026-05-06",
                "10:03:00",
                "blocked_ai_score",
                record_id=21,
                fields={"score": "50", "reason": "ai_score_50_buy_hold_override"},
            ),
            _event("2026-05-06", "10:04:00", "wait65_79_ev_candidate", record_id=22, fields={"ai_score": "74"}),
        ]
    )
    _write_events(tmp_path, "2026-05-06", current_rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert report["baseline"]["date"] == "2026-05-04"
    assert report["classification"]["primary"] == "UPSTREAM_AI_THRESHOLD"
    assert report["current"]["session"]["ratios"]["budget_to_ai_unique_pct"] == 10.0
    blocker_labels = [item["label"] for item in report["current"]["session"]["blocker_top"]]
    assert "blocked_ai_score:score_65" in blocker_labels
    assert "blocked_ai_score:ai_score_50_buy_hold_override" in blocker_labels


def test_latency_drought_when_budget_pass_exists_but_no_submitted(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(_event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx))
        rows.append(_event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx))
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx,
                fields={"reason": "latency_state_danger"},
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert report["classification"]["primary"] == "LATENCY_DROUGHT"
    assert report["current"]["session"]["stage_unique"]["budget_pass"] == 5
    assert report["current"]["session"]["stage_unique"]["order_bundle_submitted"] == 0


def test_manual_and_test_events_are_excluded(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "ai_confirmed", name="제룡전기", code="033100", record_id=1),
            _event("2026-05-06", "10:01:00", "ai_confirmed", name="TEST", code="123456", record_id=2),
            _event("2026-05-06", "10:02:00", "ai_confirmed", name="정상종목", code="000003", record_id=3),
            _event(
                "2026-05-06",
                "10:02:10",
                "holding_started",
                name="정상종목",
                code="000003",
                record_id=3,
                pipeline="HOLDING_PIPELINE",
            ),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["current"]["session"]["stage_unique"]["ai_confirmed"] == 1
    assert report["current"]["session"]["stage_unique"]["holding_started"] == 1


def test_notify_admin_skips_normal_reports(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    called = []
    report = {
        "target_date": "2026-05-06",
        "classification": {"primary": "NORMAL", "secondary": []},
    }

    monkeypatch.setattr(sentinel, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(sentinel, "_send_telegram", lambda *args: called.append(args))

    result = sentinel.maybe_notify_admin(report, {"markdown": "report.md"}, enabled=True)

    assert result == {"enabled": True, "status": "skipped", "reason": "normal"}
    assert called == []


def test_notify_admin_sends_abnormal_reports(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    called = []
    report = {
        "target_date": "2026-05-06",
        "as_of": "2026-05-06T10:00:00",
        "classification": {"primary": "LATENCY_DROUGHT", "secondary": []},
        "recommended_actions": ["check latency"],
        "policy": {"forbidden_automations": ["bot_restart"]},
        "current": {
            "session": {
                "ratios": {"budget_to_ai_unique_pct": 100.0, "submitted_to_ai_unique_pct": 0.0},
                "stage_unique": {
                    "ai_confirmed": 5,
                    "budget_pass": 5,
                    "latency_pass": 0,
                    "order_bundle_submitted": 0,
                },
                "blocker_top": [],
                "upstream_blocker_top": [],
                "latency_blocker_top": [],
                "price_guard_top": [],
            }
        },
    }

    monkeypatch.setattr(sentinel, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(sentinel, "_send_telegram", lambda *args: called.append(args))

    result = sentinel.maybe_notify_admin(report, {"markdown": "report.md"}, enabled=True)

    assert result == {"enabled": True, "status": "sent", "reason": ""}
    assert len(called) == 1


def test_notify_admin_deduplicates_until_normal_reset(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    called = []
    report = {
        "target_date": "2026-05-06",
        "as_of": "2026-05-06T10:00:00",
        "classification": {"primary": "LATENCY_DROUGHT", "secondary": []},
        "recommended_actions": ["check latency"],
        "policy": {"forbidden_automations": ["bot_restart"]},
        "current": {
            "session": {
                "ratios": {"budget_to_ai_unique_pct": 100.0, "submitted_to_ai_unique_pct": 0.0},
                "stage_unique": {
                    "ai_confirmed": 5,
                    "budget_pass": 5,
                    "latency_pass": 0,
                    "order_bundle_submitted": 0,
                },
                "blocker_top": [],
                "upstream_blocker_top": [],
                "latency_blocker_top": [],
                "price_guard_top": [],
            }
        },
    }
    normal_report = {
        "target_date": "2026-05-06",
        "as_of": "2026-05-06T10:05:00",
        "classification": {"primary": "NORMAL", "secondary": []},
    }

    monkeypatch.setattr(sentinel, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(sentinel, "_send_telegram", lambda *args: called.append(args))

    first = sentinel.maybe_notify_admin(report, {"markdown": "report.md"}, enabled=True)
    duplicate = sentinel.maybe_notify_admin(report, {"markdown": "report.md"}, enabled=True)
    normal = sentinel.maybe_notify_admin(normal_report, {"markdown": "report.md"}, enabled=True)
    after_reset = sentinel.maybe_notify_admin(report, {"markdown": "report.md"}, enabled=True)

    assert first == {"enabled": True, "status": "sent", "reason": ""}
    assert duplicate == {"enabled": True, "status": "skipped", "reason": "duplicate_signature"}
    assert normal == {"enabled": True, "status": "skipped", "reason": "normal"}
    assert after_reset == {"enabled": True, "status": "sent", "reason": ""}
    assert len(called) == 2


def test_telegram_message_is_concise_korean_summary():
    report = {
        "target_date": "2026-05-06",
        "as_of": "2026-05-06T15:20:13",
        "classification": {"primary": "UPSTREAM_AI_THRESHOLD", "secondary": ["LATENCY_DROUGHT"]},
        "recommended_actions": ["review"],
        "policy": {"forbidden_automations": ["bot_restart"]},
        "baseline": {
            "summary": {
                "ratios": {
                    "budget_to_ai_unique_pct": 78.3,
                    "submitted_to_ai_unique_pct": 38.9,
                }
            }
        },
        "current": {
            "session": {
                "ratios": {"budget_to_ai_unique_pct": 25.2, "submitted_to_ai_unique_pct": 5.4},
                "stage_unique": {
                    "ai_confirmed": 111,
                    "budget_pass": 28,
                    "latency_pass": 6,
                    "order_bundle_submitted": 6,
                },
                "blocker_top": [],
                "upstream_blocker_top": [
                    {"label": "wait65_79_ev_candidate:score_65.0", "count": 378},
                    {"label": "blocked_ai_score:score_65.0", "count": 373},
                    {"label": "blocked_ai_score:ai_score_50_buy_hold_override", "count": 281},
                ],
                "latency_blocker_top": [{"label": "latency_block:latency_state_danger", "count": 838}],
                "price_guard_top": [],
            }
        },
    }

    message = sentinel.build_telegram_message(report, {"markdown": "report.md"})

    assert "BUY 병목 이상치" in message
    assert "AI 기준/대기 병목 + 지연 가드 병목" in message
    assert "AI 111 -> 예산 28(25.2%, 기준 78.3%) -> 제출 6(5.4%, 기준 38.9%)" in message
    assert "금지된 자동변경" not in message
    assert "top_blockers" not in message
