import json

from src.engine import openai_ws_stability_report as mod


def _event(idx: int, *, transport: str = "responses_ws", error: str | None = None, ai_ms: int = 1200) -> dict:
    fields = {
        "ai_model": "gpt-5-nano",
        "openai_transport_mode": transport,
        "openai_request_id": f"{transport}:{idx}",
        "openai_endpoint_name": "analyze_target",
        "ai_prompt_type": "scalping_entry",
        "openai_ws_used": transport == "responses_ws",
        "openai_ws_http_fallback": False,
        "ai_response_ms": ai_ms,
        "openai_ws_roundtrip_ms": ai_ms - 50,
        "openai_ws_queue_wait_ms": 0,
    }
    if error:
        fields["openai_ws_error_type"] = error
    return {
        "stage": "ai_confirmed",
        "stock_code": f"{idx:06d}",
        "emitted_at": f"2026-05-14T09:{idx % 60:02d}:00",
        "fields": fields,
    }


def test_openai_ws_report_keeps_ws_for_low_rate_timeout_warnings(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True)
    rows = [_event(idx, error="TimeoutError" if idx in {10, 20} else None) for idx in range(300)]
    rows.extend(_event(1000 + idx, transport="http", ai_ms=3000) for idx in range(20))
    (event_dir / "pipeline_events_2026-05-14.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows),
        encoding="utf-8",
    )

    report = mod.build_report("2026-05-14")

    assert report["decision"] == "keep_ws"
    assert report["transport_warning"]["ws_error_count"] == 2
    assert report["transport_warning"]["warning_only"] is True


def test_openai_ws_report_rolls_back_for_high_rate_transport_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True)
    rows = [_event(idx, error="TimeoutError" if idx < 10 else None) for idx in range(60)]
    rows.extend(_event(1000 + idx, transport="http", ai_ms=3000) for idx in range(20))
    (event_dir / "pipeline_events_2026-05-14.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows),
        encoding="utf-8",
    )

    report = mod.build_report("2026-05-14")

    assert report["decision"] == "rollback_http"
    assert report["transport_warning"]["ws_error_count"] == 10
    assert report["transport_warning"]["warning_only"] is False
