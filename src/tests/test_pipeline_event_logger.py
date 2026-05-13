import json
from types import SimpleNamespace

from src.utils import pipeline_event_logger as logger_mod


def test_emit_pipeline_event_writes_text_and_jsonl(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=True,
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    payload = logger_mod.emit_pipeline_event(
        "HOLDING_PIPELINE",
        "테스트종목",
        "123456",
        "bad_entry_block_observed",
        record_id=77,
        fields={"reason": "time stop", "profit_rate": "+0.5"},
    )

    assert emitted_messages
    assert emitted_messages[0].startswith("[HOLDING_PIPELINE] 테스트종목(123456) stage=bad_entry_block_observed")
    assert "id=77" in emitted_messages[0]
    assert "reason=time|stop" in emitted_messages[0]

    out_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    assert out_path.exists()
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and rows[0]["schema_version"] == 3
    assert rows[0]["pipeline"] == "HOLDING_PIPELINE"
    assert rows[0]["record_id"] == 77
    assert rows[0]["fields"]["reason"] == "time stop"

    compact_path = tmp_path / "threshold_cycle" / f"threshold_events_{payload['emitted_date']}.jsonl"
    assert compact_path.exists()
    compact_rows = [json.loads(line) for line in compact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert compact_rows and compact_rows[0]["event_type"] == "threshold_cycle_event"
    assert compact_rows[0]["stage"] == "bad_entry_block_observed"


def test_emit_pipeline_event_suppresses_default_text_info_but_keeps_jsonl(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "blocked_strength_momentum",
        record_id=77,
        fields={"reason": "below_strength_base", "ai_score": "50"},
    )

    assert emitted_messages == []
    out_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and rows[0]["stage"] == "blocked_strength_momentum"
    assert rows[0]["text_payload"].startswith("[ENTRY_PIPELINE] 테스트종목(123456)")
    assert rows[0]["fields"]["reason"] == "below_strength_base"


def test_emit_pipeline_event_allowlist_keeps_operational_text_info(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=("order_bundle_submitted",),
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "order_bundle_submitted",
        fields={"actual_order_submitted": "True"},
    )

    assert len(emitted_messages) == 1
    assert "stage=order_bundle_submitted" in emitted_messages[0]


def test_emit_pipeline_event_suppresses_non_real_order_text_info(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=("order_bundle_submitted",),
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "order_bundle_submitted",
        fields={"actual_order_submitted": "False", "simulated_order": "True"},
    )

    assert emitted_messages == []
    out_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and rows[0]["stage"] == "order_bundle_submitted"
    assert rows[0]["fields"]["actual_order_submitted"] == "False"


def test_emit_pipeline_event_writes_reversal_add_gate_blocked_to_compact_stream(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)

    payload = logger_mod.emit_pipeline_event(
        "HOLDING_PIPELINE",
        "테스트종목",
        "123456",
        "reversal_add_gate_blocked",
        record_id=78,
        fields={"gate_reason": "position_at_cap"},
    )

    compact_path = tmp_path / "threshold_cycle" / f"threshold_events_{payload['emitted_date']}.jsonl"
    compact_rows = [json.loads(line) for line in compact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert compact_rows and compact_rows[0]["stage"] == "reversal_add_gate_blocked"


def test_emit_pipeline_event_accepts_dynamic_threshold_family(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "new_threshold_probe",
        fields={"threshold_family": "entry_new_probe", "value": "1"},
    )

    compact_path = tmp_path / "threshold_cycle" / f"threshold_events_{payload['emitted_date']}.jsonl"
    compact_rows = [json.loads(line) for line in compact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert compact_rows and compact_rows[0]["stage"] == "new_threshold_probe"
    assert compact_rows[0]["family"] == "entry_new_probe"
