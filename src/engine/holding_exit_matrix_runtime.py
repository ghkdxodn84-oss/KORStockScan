from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR


MATRIX_DIR = DATA_DIR / "report" / "holding_exit_decision_matrix"
MATRIX_FILE_RE = re.compile(r"holding_exit_decision_matrix_(\d{4}-\d{2}-\d{2})\.json$")


def _price_bucket(value: Any) -> str:
    try:
        price = float(value)
    except Exception:
        price = 0.0
    if price <= 0:
        return "price_unknown"
    if price < 10_000:
        return "price_lt_10k"
    if price < 30_000:
        return "price_10k_30k"
    if price < 70_000:
        return "price_30k_70k"
    return "price_gte_70k"


def _volume_bucket(value: Any) -> str:
    try:
        volume = float(value)
    except Exception:
        volume = 0.0
    if volume <= 0:
        return "volume_unknown"
    if volume < 500_000:
        return "volume_lt_500k"
    if volume < 2_000_000:
        return "volume_500k_2m"
    if volume < 10_000_000:
        return "volume_2m_10m"
    return "volume_gte_10m"


def _time_bucket(value: datetime | None) -> str:
    if value is None:
        return "time_unknown"
    minute = value.hour * 60 + value.minute
    if minute < 9 * 60 or minute >= 15 * 60 + 30:
        return "time_outside_regular"
    if minute < 9 * 60 + 30:
        return "time_0900_0930"
    if minute < 10 * 60 + 30:
        return "time_0930_1030"
    if minute < 14 * 60:
        return "time_1030_1400"
    return "time_1400_1530"


def _session_cutoff_source_date(now: datetime) -> date:
    if now.hour >= 16:
        return now.date()
    return now.date() - timedelta(days=1)


def _latest_matrix_path_on_or_before(target_date: date) -> Path | None:
    best_date: date | None = None
    best_path: Path | None = None
    if not MATRIX_DIR.exists():
        return None
    for path in MATRIX_DIR.glob("holding_exit_decision_matrix_*.json"):
        match = MATRIX_FILE_RE.match(path.name)
        if not match:
            continue
        try:
            current_date = date.fromisoformat(match.group(1))
        except ValueError:
            continue
        if current_date > target_date:
            continue
        if best_date is None or current_date > best_date:
            best_date = current_date
            best_path = path
    return best_path


def _read_matrix_payload(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_intraday_volume(ws_data: dict[str, Any] | None, recent_candles: list[dict[str, Any]] | None) -> Any:
    ws = ws_data or {}
    for key in ("volume", "today_vol", "acc_volume", "trade_volume"):
        value = ws.get(key)
        if value not in (None, "", 0, 0.0):
            return value
    candles = recent_candles or []
    if candles:
        latest = candles[-1] if isinstance(candles[-1], dict) else {}
        for key in ("누적거래량", "누적 거래량", "acc_volume", "volume", "거래량"):
            value = latest.get(key)
            if value not in (None, "", 0, 0.0):
                return value
    return 0


def _matched_entries(payload: dict[str, Any], buckets: dict[str, str]) -> list[dict[str, Any]]:
    by_axis = {
        str(entry.get("axis") or ""): entry
        for entry in (payload.get("entries") or [])
        if isinstance(entry, dict)
    }
    matched: list[dict[str, Any]] = []
    for axis_name in ("price_bucket", "volume_bucket", "time_bucket"):
        bucket = buckets.get(axis_name, f"{axis_name}_unknown")
        entry = by_axis.get(axis_name)
        if entry and str(entry.get("bucket") or "") == bucket:
            matched.append(entry)
            continue
        matched.append(
            {
                "axis": axis_name,
                "bucket": bucket,
                "recommended_bias": "no_clear_edge",
                "policy_hint": "runtime_bucket_unmapped",
                "prompt_hint": f"{axis_name}={bucket} runtime bucket은 matrix entry가 없어 기존 보유/청산 원칙을 우선한다.",
            }
        )
    return matched


def _prompt_context(payload: dict[str, Any], matched_entries: list[dict[str, Any]]) -> str:
    if not payload:
        return ""
    hard_veto = ", ".join(str(item) for item in (payload.get("hard_veto") or [])[:4]) or "-"
    lines = [
        "[ADM Advisory Context]",
        "- source: report-only holding/exit decision matrix. hard veto and existing runtime safety always win.",
        f"- matrix_version: {payload.get('matrix_version', '-')}",
        f"- source_date: {payload.get('source_date', '-')}",
        f"- hard_veto_first: {hard_veto}",
        "- matched_buckets:",
    ]
    for entry in matched_entries:
        lines.append(
            "  - "
            f"{entry.get('axis')}={entry.get('bucket')} / bias={entry.get('recommended_bias', '-')} / "
            f"policy={entry.get('policy_hint', '-')}"
        )
    lines.append("- prompt_hints:")
    for entry in matched_entries:
        lines.append(f"  - {entry.get('prompt_hint', '-')}")
    lines.append("- rules: keep the existing HOLD/TRIM/EXIT schema. if bias is no_clear_edge, prefer the baseline rule.")
    return "\n".join(lines)


def _alignment_for_action(action_label: str, matched_entries: list[dict[str, Any]]) -> str:
    action = str(action_label or "").upper()
    biases = {str(entry.get("recommended_bias") or "no_clear_edge") for entry in matched_entries}
    if not action:
        return "unknown_action"
    if biases == {"no_clear_edge"}:
        return "neutral_no_clear_edge"
    if "prefer_exit" in biases and action in {"EXIT", "TRIM", "DROP", "SELL"}:
        return "aligned_exit_bias"
    if biases & {"prefer_avg_down_wait", "prefer_pyramid_wait"} and action in {"HOLD", "WAIT"}:
        return "aligned_wait_bias"
    if action in {"HOLD", "WAIT"}:
        return "hold_against_matrix_bias"
    if action in {"EXIT", "TRIM", "DROP", "SELL"}:
        return "exit_against_matrix_bias"
    return "mixed_or_unknown"


def build_holding_exit_matrix_runtime_context(
    *,
    prompt_profile: str,
    ws_data: dict[str, Any] | None,
    recent_candles: list[dict[str, Any]] | None,
    advisory_enabled: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    profile = str(prompt_profile or "shared").strip().lower()
    current_dt = now or datetime.now()
    price_bucket = _price_bucket((ws_data or {}).get("curr") or (ws_data or {}).get("curr_price"))
    volume_bucket = _volume_bucket(_resolve_intraday_volume(ws_data, recent_candles))
    time_bucket = _time_bucket(current_dt)
    buckets = {
        "price_bucket": price_bucket,
        "volume_bucket": volume_bucket,
        "time_bucket": time_bucket,
    }
    if profile not in {"holding", "exit"}:
        return {
            "applied": False,
            "status": "excluded_non_holding_prompt",
            "cohort": "excluded",
            "cache_token": f"excluded:non_holding:{price_bucket}:{volume_bucket}:{time_bucket}",
            "prompt_context": "",
            "fields": {
                "holding_exit_matrix_feature_enabled": bool(advisory_enabled),
                "holding_exit_matrix_applied": False,
                "holding_exit_matrix_status": "excluded_non_holding_prompt",
                "holding_exit_matrix_cohort": "excluded",
                "holding_exit_matrix_version": "-",
                "holding_exit_matrix_source_date": "-",
                "holding_exit_matrix_valid_for_date": "-",
                "holding_exit_matrix_application_mode": "-",
                "holding_exit_matrix_loaded_from": "-",
                "holding_exit_matrix_cache_token": f"excluded:non_holding:{price_bucket}:{volume_bucket}:{time_bucket}",
                "holding_exit_matrix_price_bucket": price_bucket,
                "holding_exit_matrix_volume_bucket": volume_bucket,
                "holding_exit_matrix_time_bucket": time_bucket,
                "holding_exit_matrix_recommended_biases": "-",
                "holding_exit_matrix_policy_hints": "-",
            },
            "matched_entries": [],
        }

    matrix_path = _latest_matrix_path_on_or_before(_session_cutoff_source_date(current_dt))
    payload = _read_matrix_payload(matrix_path)
    if not payload:
        status = "matrix_missing_or_invalid"
        cohort = "excluded"
        cache_token = f"excluded:missing:{price_bucket}:{volume_bucket}:{time_bucket}"
        return {
            "applied": False,
            "status": status,
            "cohort": cohort,
            "cache_token": cache_token,
            "prompt_context": "",
            "fields": {
                "holding_exit_matrix_feature_enabled": bool(advisory_enabled),
                "holding_exit_matrix_applied": False,
                "holding_exit_matrix_status": status,
                "holding_exit_matrix_cohort": cohort,
                "holding_exit_matrix_version": "-",
                "holding_exit_matrix_source_date": "-",
                "holding_exit_matrix_valid_for_date": "-",
                "holding_exit_matrix_application_mode": "-",
                "holding_exit_matrix_loaded_from": str(matrix_path) if matrix_path is not None else "-",
                "holding_exit_matrix_cache_token": cache_token,
                "holding_exit_matrix_price_bucket": price_bucket,
                "holding_exit_matrix_volume_bucket": volume_bucket,
                "holding_exit_matrix_time_bucket": time_bucket,
                "holding_exit_matrix_recommended_biases": "-",
                "holding_exit_matrix_policy_hints": "-",
            },
            "matched_entries": [],
        }

    matched_entries = _matched_entries(payload, buckets)
    cohort = "candidate" if advisory_enabled else "baseline"
    status = "advisory_prompt_applied" if advisory_enabled else "loaded_feature_disabled"
    matrix_version = str(payload.get("matrix_version") or "-")
    source_date = str(payload.get("source_date") or "-")
    valid_for_date = str(payload.get("valid_for_date") or "-")
    application_mode = str(payload.get("application_mode") or "-")
    cache_token = (
        f"{cohort}:{matrix_version}:{price_bucket}:{volume_bucket}:{time_bucket}"
    )
    fields = {
        "holding_exit_matrix_feature_enabled": bool(advisory_enabled),
        "holding_exit_matrix_applied": bool(advisory_enabled),
        "holding_exit_matrix_status": status,
        "holding_exit_matrix_cohort": cohort,
        "holding_exit_matrix_version": matrix_version,
        "holding_exit_matrix_source_date": source_date,
        "holding_exit_matrix_valid_for_date": valid_for_date,
        "holding_exit_matrix_application_mode": application_mode,
        "holding_exit_matrix_loaded_from": str(matrix_path),
        "holding_exit_matrix_cache_token": cache_token,
        "holding_exit_matrix_price_bucket": price_bucket,
        "holding_exit_matrix_volume_bucket": volume_bucket,
        "holding_exit_matrix_time_bucket": time_bucket,
        "holding_exit_matrix_recommended_biases": ",".join(
            str(entry.get("recommended_bias") or "no_clear_edge") for entry in matched_entries
        ),
        "holding_exit_matrix_policy_hints": ",".join(
            str(entry.get("policy_hint") or "-") for entry in matched_entries
        ),
    }
    return {
        "applied": bool(advisory_enabled),
        "status": status,
        "cohort": cohort,
        "cache_token": cache_token,
        "prompt_context": _prompt_context(payload, matched_entries) if advisory_enabled else "",
        "fields": fields,
        "matched_entries": matched_entries,
    }


def merge_holding_exit_matrix_result_fields(
    result: dict[str, Any] | None,
    runtime_context: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(result or {})
    context = runtime_context or {}
    fields = dict(context.get("fields") or {})
    action = payload.get("action_v2") or payload.get("action") or ""
    fields["holding_exit_matrix_decision_alignment"] = _alignment_for_action(
        str(action or ""),
        list(context.get("matched_entries") or []),
    )
    payload.update(fields)
    return payload
