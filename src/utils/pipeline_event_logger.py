"""Common pipeline-event logger for text logs and structured JSONL events."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.logger import log_error, log_info
from src.utils.threshold_cycle_registry import threshold_family_for_stage
from src.engine.dashboard_data_repository import upsert_pipeline_event_rows


_WRITE_LOCK = threading.RLock()

_TEXT_INFO_STAGE_KEYWORDS = (
    "order_submitted",
    "order_bundle_submitted",
    "order_sent",
    "order_cancel",
    "order_failed",
    "order_rejected",
    "sell_order",
    "hard_stop",
    "protect",
    "emergency",
)


def _event_dir() -> Path:
    path = DATA_DIR / "pipeline_events"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _event_path(target_date: str) -> Path:
    return _event_dir() / f"pipeline_events_{target_date}.jsonl"


def _threshold_cycle_dir() -> Path:
    path = DATA_DIR / "threshold_cycle"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _threshold_cycle_event_path(target_date: str) -> Path:
    return _threshold_cycle_dir() / f"threshold_events_{target_date}.jsonl"


def sanitize_pipeline_field(value) -> str:
    return str(value).replace(" ", "|")


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _falsey(value) -> bool:
    return str(value).strip().lower() in {"0", "false", "no", "n", "off"}


def _is_non_real_observation(stage: str, fields: dict | None) -> bool:
    raw_fields = fields or {}
    lowered_stage = str(stage or "").strip().lower()
    if _falsey(raw_fields.get("actual_order_submitted")):
        return True
    if _truthy(raw_fields.get("broker_order_forbidden")):
        return True
    if _truthy(raw_fields.get("simulated_order")):
        return True
    if raw_fields.get("simulation_book") or raw_fields.get("simulation_owner"):
        return True
    if _truthy(raw_fields.get("swing_intraday_probe")):
        return True
    if raw_fields.get("probe_id") or raw_fields.get("probe_origin_stage"):
        return True
    return "sim_" in lowered_stage or "_probe_" in lowered_stage or lowered_stage.startswith("swing_probe_")


def _should_emit_text_info(stage: str, fields: dict | None) -> bool:
    if bool(getattr(TRADING_RULES, "PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED", False)):
        return True

    safe_stage = str(stage or "").strip()
    raw_fields = fields or {}
    if _is_non_real_observation(safe_stage, raw_fields):
        return False

    allowlist = tuple(getattr(TRADING_RULES, "PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST", ()) or ())
    if safe_stage in allowlist:
        return True

    lowered_stage = safe_stage.lower()
    if any(keyword in lowered_stage for keyword in _TEXT_INFO_STAGE_KEYWORDS):
        return True

    if _truthy(raw_fields.get("actual_order_submitted")):
        return True
    if _truthy(raw_fields.get("broker_order_submitted")):
        return True

    return False


def emit_pipeline_event(
    pipeline: str,
    name: str,
    code: str,
    stage: str,
    *,
    record_id=None,
    fields: dict | None = None,
) -> dict:
    """Emit legacy text log + structured JSONL event with a shared schema."""
    safe_pipeline = str(pipeline or "").strip() or "PIPELINE"
    safe_name = str(name or "").strip() or "-"
    safe_code = str(code or "").strip()[:6] or "-"
    safe_stage = str(stage or "").strip() or "-"

    merged_fields = {}
    if record_id not in (None, "", 0):
        merged_fields["id"] = record_id
    merged_fields.update(fields or {})

    parts = [f"{key}={sanitize_pipeline_field(value)}" for key, value in merged_fields.items()]
    suffix = f" {' '.join(parts)}" if parts else ""
    text_payload = f"[{safe_pipeline}] {safe_name}({safe_code}) stage={safe_stage}{suffix}"
    if _should_emit_text_info(safe_stage, fields or {}):
        log_info(text_payload)

    event_payload = {
        "schema_version": int(getattr(TRADING_RULES, "PIPELINE_EVENT_SCHEMA_VERSION", 1) or 1),
        "event_type": "pipeline_event",
        "pipeline": safe_pipeline,
        "stage": safe_stage,
        "stock_name": safe_name,
        "stock_code": safe_code,
        "record_id": int(record_id) if record_id not in (None, "", 0) else None,
        "fields": {str(key): str(value) for key, value in (fields or {}).items()},
        "emitted_at": datetime.now().isoformat(),
        "emitted_date": datetime.now().strftime("%Y-%m-%d"),
        "text_payload": text_payload,
    }

    if not bool(getattr(TRADING_RULES, "PIPELINE_EVENT_JSONL_ENABLED", True)):
        return event_payload

    try:
        with _WRITE_LOCK:
            path = _event_path(event_payload["emitted_date"])
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(event_payload, ensure_ascii=False) + "\n")
            threshold_family = threshold_family_for_stage(safe_stage, event_payload["fields"])
            if threshold_family:
                compact_payload = {
                    "schema_version": 1,
                    "event_type": "threshold_cycle_event",
                    "family": threshold_family,
                    "pipeline": safe_pipeline,
                    "stage": safe_stage,
                    "stock_name": safe_name,
                    "stock_code": safe_code,
                    "record_id": int(record_id) if record_id not in (None, "", 0) else None,
                    "fields": {str(key): str(value) for key, value in (fields or {}).items()},
                    "emitted_at": event_payload["emitted_at"],
                    "emitted_date": event_payload["emitted_date"],
                }
                compact_path = _threshold_cycle_event_path(event_payload["emitted_date"])
                with open(compact_path, "a", encoding="utf-8") as compact_handle:
                    compact_handle.write(json.dumps(compact_payload, ensure_ascii=False) + "\n")
    except Exception as exc:
        log_error(f"[PIPELINE_EVENT] structured append failed: {exc}")

    # DB 저장 시도
    try:
        upsert_pipeline_event_rows(event_payload["emitted_date"], [event_payload])
    except Exception as exc:
        log_error(f"[PIPELINE_EVENT] DB upsert failed: {exc}")

    return event_payload
