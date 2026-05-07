import json

from src.engine import holding_exit_sentinel as sentinel


def _event(
    target_date: str,
    hhmmss: str,
    stage: str,
    *,
    record_id: int = 1,
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "HOLDING_PIPELINE",
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
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


def _write_observation(tmp_path, target_date: str, payload: dict) -> None:
    report_dir = tmp_path / "report" / "monitor_snapshots"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"holding_exit_observation_{target_date}.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def test_sell_execution_drought_when_exit_signal_not_sent(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "exit_signal", record_id=1),
            _event("2026-05-06", "10:01:00", "exit_signal", record_id=2),
            _event("2026-05-06", "10:01:05", "sell_order_sent", record_id=1),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["classification"]["primary"] == "SELL_EXECUTION_DROUGHT"
    assert report["current"]["session"]["stage_unique"]["exit_signal"] == 2
    assert report["current"]["session"]["stage_unique"]["sell_order_sent"] == 1


def test_hold_defer_danger_is_classified(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "2026-05-06",
            f"10:0{idx}:00",
            "holding_flow_override_defer_exit",
            record_id=idx,
            fields={"worsen_pct": "0.35", "exit_rule": "scalp_ai_early_exit"},
        )
        for idx in range(3)
    ]
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["classification"]["primary"] == "HOLD_DEFER_DANGER"


def test_observation_flags_soft_stop_and_trailing(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(tmp_path, "2026-05-06", [_event("2026-05-06", "10:00:00", "holding_started")])
    _write_observation(
        tmp_path,
        "2026-05-06",
        {
            "soft_stop_rebound": {"total_soft_stop": 5, "rebound_above_sell_10m_rate": 80.0},
            "exit_rule_quality": [
                {
                    "exit_rule": "scalp_trailing_take_profit",
                    "evaluated_post_sell": 5,
                    "missed_upside_rate": 40.0,
                }
            ],
        },
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["classification"]["primary"] == "SOFT_STOP_WHIPSAW"
    assert "TRAILING_EARLY_EXIT" in report["classification"]["secondary"]


def test_stale_after_all_positions_completed_is_not_runtime_ops(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "holding_started", record_id=1),
            _event("2026-05-06", "10:01:00", "ai_holding_review", record_id=1, fields={"ai_cache": "miss"}),
            _event("2026-05-06", "10:02:00", "sell_completed", record_id=1),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:30:00"),
    )

    assert report["current"]["session"]["unique_symbols"]["active_holding"] == 0
    assert "RUNTIME_OPS" not in report["classification"]["matches"]


def test_stale_with_active_holding_is_runtime_ops(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "holding_started", record_id=1),
            _event("2026-05-06", "10:01:00", "ai_holding_review", record_id=1, fields={"ai_cache": "miss"}),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:30:00"),
    )

    assert report["current"]["session"]["unique_symbols"]["active_holding"] == 1
    assert report["classification"]["primary"] == "RUNTIME_OPS"


def test_notify_admin_skips_normal(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    called = []
    report = {"target_date": "2026-05-06", "classification": {"primary": "NORMAL", "secondary": []}}
    monkeypatch.setattr(sentinel, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(sentinel, "_send_telegram", lambda *args: called.append(args))

    result = sentinel.maybe_notify_admin(report, {"markdown": "report.md"}, enabled=True)

    assert result == {"enabled": True, "status": "skipped", "reason": "normal"}
    assert called == []


def test_notify_admin_deduplicates_until_normal_reset(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    called = []
    report = {
        "target_date": "2026-05-06",
        "as_of": "2026-05-06T10:05:00",
        "classification": {"primary": "HOLD_DEFER_DANGER", "secondary": ["AI_HOLDING_OPS"]},
        "current": {
            "session": {
                "stage_unique": {"exit_signal": 2, "sell_order_sent": 2, "sell_completed": 1},
                "stage_events": {"holding_flow_override_defer_exit": 3},
                "ratios": {"sell_sent_to_exit_signal_unique_pct": 100.0, "ai_cache_miss_pct": 95.0},
            }
        },
        "observation": {"metrics": {}},
    }
    normal_report = {
        "target_date": "2026-05-06",
        "as_of": "2026-05-06T10:10:00",
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
        "as_of": "2026-05-06T10:05:00",
        "classification": {"primary": "HOLD_DEFER_DANGER", "secondary": ["AI_HOLDING_OPS"]},
        "current": {
            "session": {
                "stage_unique": {"exit_signal": 2, "sell_order_sent": 2, "sell_completed": 1},
                "stage_events": {"holding_flow_override_defer_exit": 3},
                "ratios": {"sell_sent_to_exit_signal_unique_pct": 100.0, "ai_cache_miss_pct": 95.0},
            }
        },
        "observation": {
            "metrics": {
                "soft_stop_rebound_above_sell_10m_rate": 80.0,
                "trailing_missed_upside_rate": 40.0,
            }
        },
    }

    message = sentinel.build_telegram_message(report, {"markdown": "report.md"})

    assert "HOLD/EXIT 이상치" in message
    assert "HOLD 유예 악화 + AI 보유감시 이상" in message
    assert "자동조치: 없음" in message
