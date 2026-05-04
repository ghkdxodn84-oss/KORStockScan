from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from datetime import datetime, time
from pathlib import Path
from typing import Any, Iterable


ENTRY_PIPELINE = "ENTRY_PIPELINE"
HOLDING_PIPELINE = "HOLDING_PIPELINE"
ENTRY_BASELINE_N_MIN = 50
ENTRY_SUBMITTED_MIN = 20
SOFT_STOP_GRACE_MIN = 10
VALID_COMPLETED_MIN = 10
SIGNAL_QUALITY_QUOTE_MIN_SIGNAL = 90.0
SIGNAL_QUALITY_QUOTE_MIN_STRENGTH = 110.0
SIGNAL_QUALITY_QUOTE_MIN_BUY_PRESSURE = 65.0
SIGNAL_QUALITY_QUOTE_MAX_WS_AGE_MS = 1200
SIGNAL_QUALITY_QUOTE_MAX_WS_JITTER_MS = 500
SIGNAL_QUALITY_QUOTE_MAX_SPREAD_RATIO = 0.0085
GATEKEEPER_DECISION_STAGES = {
    "blocked_gatekeeper_reject",
    "market_regime_pass",
    "blocked_gatekeeper_error",
}
ENTRY_ARMED_STAGES = {"entry_armed", "entry_armed_resume"}
REUSE_REASON_LABELS = {
    "sig_changed": "signature_changed",
    "age_expired": "reuse_window_expired",
    "ws_stale": "ws_stale",
    "price_move": "price_move",
    "near_ai_exit": "near_ai_exit",
    "near_safe_profit": "near_safe_profit",
    "near_low_score": "near_low_score",
    "score_boundary": "score_boundary",
    "missing_action": "missing_action",
    "missing_allow_flag": "missing_allow_flag",
}


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    return datetime.strptime(value, "%H:%M:%S").time()


def _parse_dt(value: object) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _row_time(row: dict[str, Any]) -> time | None:
    sell_time = str(row.get("sell_time") or "").strip()
    if sell_time:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(sell_time, fmt).time()
            except ValueError:
                continue
    dt = _parse_dt(row.get("emitted_at") or row.get("recorded_at") or row.get("evaluated_at"))
    return dt.time() if dt is not None else None


def _row_date(row: dict[str, Any]) -> str:
    for key in ("emitted_date", "signal_date"):
        value = str(row.get(key) or "").strip()
        if value:
            return value[:10]
    dt = _parse_dt(row.get("emitted_at") or row.get("recorded_at") or row.get("evaluated_at"))
    return dt.date().isoformat() if dt is not None else ""


def _in_window(row: dict[str, Any], since: time | None, until: time | None, target_date: str | None = None) -> bool:
    if target_date and _row_date(row) != target_date:
        return False
    row_t = _row_time(row)
    if row_t is None:
        return False
    if since is not None and row_t < since:
        return False
    if until is not None and row_t > until:
        return False
    return True


def _read_json(path: Path) -> Any | None:
    try:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl(
    path: Path,
    *,
    since: time | None = None,
    until: time | None = None,
    target_date: str | None = None,
    break_after_until: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    if target_date and _row_date(row) != target_date:
                        continue
                    if since is not None or until is not None:
                        row_t = _row_time(row)
                        if row_t is None:
                            continue
                        if until is not None and row_t > until:
                            if break_after_until:
                                break
                            continue
                        if since is not None and row_t < since:
                            continue
                    rows.append(row)
    except OSError:
        return []
    return rows


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text == "-":
        return None
    try:
        return float(text.replace("%", ""))
    except ValueError:
        return None


def _truthy(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "applied"}:
        return True
    if text in {"0", "false", "no", "n", "off", "none", "-", ""}:
        return False
    return None


def _fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _field(row: dict[str, Any], *names: str) -> Any:
    fields = _fields(row)
    for name in names:
        if name in fields:
            return fields.get(name)
        if name in row:
            return row.get(name)
    return None


def _stage(row: dict[str, Any]) -> str:
    return str(row.get("stage") or "").strip()


def _pipeline(row: dict[str, Any]) -> str:
    return str(row.get("pipeline") or "").strip()


def _text_blob(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True).lower()


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    if denominator == 0:
        return None
    return round(float(numerator) / float(denominator), 6)


def _percent_point(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 100.0, 4)


def _csv_counter(value: object) -> Counter[str]:
    counter: Counter[str] = Counter()
    if value is None:
        return counter
    for item in str(value).replace("|", ",").split(","):
        token = item.strip()
        if token:
            counter[token] += 1
    return counter


def _record_id(row: dict[str, Any]) -> str:
    value = row.get("record_id")
    if value in (None, "", 0):
        value = _field(row, "id")
    return str(value or "").strip()


def _canary_applied(row: dict[str, Any]) -> bool | None:
    for key in (
        "quote_fresh_composite_canary_applied",
        "latency_quote_fresh_composite_canary_applied",
        "composite_canary_applied",
    ):
        state = _truthy(_field(row, key))
        if state is not None:
            return state
    reason = str(_field(row, "latency_canary_reason", "reason") or "").strip()
    if reason == "quote_fresh_composite_canary_applied":
        return True
    if reason == "latency_quote_fresh_composite_normal_override":
        return True
    return None


def _load_manifest(bundle_dir: Path) -> dict[str, Any]:
    manifest = _read_json(bundle_dir / "bundle_manifest.json")
    return manifest if isinstance(manifest, dict) else {}


def _load_pipeline_events(bundle_dir: Path, since: time | None, until: time | None, target_date: str | None) -> list[dict[str, Any]]:
    events_dir = bundle_dir / "data" / "pipeline_events"
    rows: list[dict[str, Any]] = []
    for path in sorted(events_dir.glob("pipeline_events_*.jsonl")):
        rows.extend(_read_jsonl(path, since=since, until=until, target_date=target_date, break_after_until=True))
    for path in sorted(events_dir.glob("pipeline_events_*.jsonl.gz")):
        rows.extend(_read_jsonl(path, since=since, until=until, target_date=target_date, break_after_until=True))
    return rows


def _load_post_sell_rows(
    bundle_dir: Path,
    since: time | None,
    until: time | None,
    target_date: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    post_sell_dir = bundle_dir / "data" / "post_sell"
    candidates: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    for path in sorted(post_sell_dir.glob("post_sell_candidates_*.jsonl")):
        candidates.extend(_read_jsonl(path, since=since, until=until, target_date=target_date))
    for path in sorted(post_sell_dir.glob("post_sell_candidates_*.jsonl.gz")):
        candidates.extend(_read_jsonl(path, since=since, until=until, target_date=target_date))
    for path in sorted(post_sell_dir.glob("post_sell_evaluations_*.jsonl")):
        evaluations.extend(_read_jsonl(path, since=since, until=until, target_date=target_date))
    for path in sorted(post_sell_dir.glob("post_sell_evaluations_*.jsonl.gz")):
        evaluations.extend(_read_jsonl(path, since=since, until=until, target_date=target_date))
    return candidates, evaluations


def _load_shadow_diff_status(bundle_dir: Path) -> str:
    data = _read_json(bundle_dir / "data" / "analytics" / "shadow_diff_summary.json")
    if not isinstance(data, dict):
        return "unavailable"
    blob = json.dumps(data, ensure_ascii=False).lower()
    if "unresolved" in blob or "mismatch" in blob:
        return "unresolved"
    return "available"


def _fill_counts(rows: Iterable[dict[str, Any]]) -> tuple[int, int]:
    full = 0
    partial = 0
    for row in rows:
        blob = _text_blob(row)
        quality = str(_field(row, "fill_quality", "fill_status") or "").strip().upper()
        if quality == "FULL" or "full_fill" in blob:
            full += 1
        elif quality == "PARTIAL" or "partial_fill" in blob:
            partial += 1
    return full, partial


def _avg(values: Iterable[float]) -> float | None:
    items = [float(value) for value in values]
    if not items:
        return None
    return round(sum(items) / len(items), 6)


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 2)
    rank = (len(ordered) - 1) * (percentile / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return round(ordered[lower] * (1.0 - weight) + ordered[upper] * weight, 2)


def _friendly_reuse_reason(reason_code: str) -> str:
    code = str(reason_code or "").strip()
    return REUSE_REASON_LABELS.get(code, code or "-")


def _count_sig_delta_fields(counter: Counter[str], raw_value: object) -> None:
    raw = str(raw_value or "").strip()
    if not raw or raw == "-":
        return
    for token in raw.split(","):
        field = token.split(":", 1)[0].strip()
        if field:
            counter[field] += 1


def _orderbook_stability_summary(
    window_rows: list[dict[str, Any]],
    holding_rows: list[dict[str, Any]],
    submitted_rows: list[dict[str, Any]],
    latency_state_danger_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    observed_rows = [row for row in window_rows if _stage(row) == "orderbook_stability_observed"]
    unstable_rows = [row for row in observed_rows if _truthy(_field(row, "unstable_quote_observed")) is True]
    unstable_ids = {_record_id(row) for row in unstable_rows if _record_id(row)}
    submitted_ids = {_record_id(row) for row in submitted_rows if _record_id(row)}
    latency_danger_ids = {_record_id(row) for row in latency_state_danger_rows if _record_id(row)}

    fill_rows = []
    for row in holding_rows:
        blob = _text_blob(row)
        quality = str(_field(row, "fill_quality", "fill_status") or "").strip().upper()
        if quality in {"FULL", "PARTIAL"} or "full_fill" in blob or "partial_fill" in blob:
            fill_rows.append(row)
    fill_ids = {_record_id(row) for row in fill_rows if _record_id(row)}

    reason_breakdown: Counter[str] = Counter()
    for row in unstable_rows:
        reason_breakdown.update(_csv_counter(_field(row, "unstable_reasons")))

    return {
        "orderbook_stability_observed_count": len(observed_rows),
        "unstable_quote_observed_count": len(unstable_rows),
        "unstable_quote_share": _percent_point(_ratio(len(unstable_rows), len(observed_rows))),
        "unstable_reason_breakdown": dict(reason_breakdown),
        "unstable_vs_submitted": {
            "unstable_record_count": len(unstable_ids),
            "submitted_count": len(unstable_ids & submitted_ids),
            "submitted_rate": _percent_point(_ratio(len(unstable_ids & submitted_ids), len(unstable_ids))),
        },
        "unstable_vs_fill": {
            "unstable_record_count": len(unstable_ids),
            "fill_count": len(unstable_ids & fill_ids),
            "fill_rate": _percent_point(_ratio(len(unstable_ids & fill_ids), len(unstable_ids))),
        },
        "unstable_vs_latency_danger": {
            "unstable_record_count": len(unstable_ids),
            "latency_danger_count": len(unstable_ids & latency_danger_ids),
            "latency_danger_rate": _percent_point(_ratio(len(unstable_ids & latency_danger_ids), len(unstable_ids))),
        },
    }


def _latency_entry_price_guard_summary(
    window_rows: list[dict[str, Any]],
    holding_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    submitted_rows = [row for row in window_rows if _stage(row) == "order_bundle_submitted"]
    guard_breakdown: Counter[str] = Counter()
    submitted_by_id: dict[str, dict[str, Any]] = {}
    for row in submitted_rows:
        guard = str(_field(row, "entry_price_guard") or "unknown").strip() or "unknown"
        guard_breakdown[guard] += 1
        record_id = _record_id(row)
        if record_id:
            submitted_by_id[record_id] = row

    three_tick_ids = {
        _record_id(row)
        for row in submitted_rows
        if str(_field(row, "entry_price_guard") or "") == "latency_danger_override_defensive"
        and _record_id(row)
    }
    full_ids = {
        _record_id(row)
        for row in holding_rows
        if _record_id(row) and (_stage(row) == "full_fill" or str(_field(row, "fill_quality", "fill_status") or "").upper() == "FULL")
    }
    partial_ids = {
        _record_id(row)
        for row in holding_rows
        if _record_id(row) and (_stage(row) == "partial_fill" or str(_field(row, "fill_quality", "fill_status") or "").upper() == "PARTIAL")
    }
    fill_ids = full_ids | partial_ids

    slippage_bps: list[float] = []
    slippage_krw: list[float] = []
    completed_profit_rates: list[float] = []
    for row in holding_rows:
        record_id = _record_id(row)
        if record_id not in three_tick_ids:
            continue
        submitted = submitted_by_id.get(record_id) or {}
        order_price = _safe_float(_field(submitted, "order_price", "latency_guarded_order_price"))
        fill_price = _safe_float(_field(row, "fill_price", "buy_price", "exec_price"))
        if order_price and fill_price:
            diff = float(fill_price) - float(order_price)
            slippage_krw.append(diff)
            slippage_bps.append(round((diff / float(order_price)) * 10_000.0, 6))
        status = str(_field(row, "status", "holding_status") or "").strip().upper()
        profit = _safe_float(_field(row, "profit_rate", "realized_profit_rate"))
        if status == "COMPLETED" and profit is not None:
            completed_profit_rates.append(float(profit))

    three_tick_fill_ids = three_tick_ids & fill_ids
    return {
        "submitted_guard_breakdown": dict(guard_breakdown),
        "three_tick_guard": {
            "submitted_count": len(three_tick_ids),
            "full_fill_count": len(three_tick_ids & full_ids),
            "partial_fill_count": len(three_tick_ids & partial_ids),
            "fill_count": len(three_tick_fill_ids),
            "fill_rate": _percent_point(_ratio(len(three_tick_fill_ids), len(three_tick_ids))),
            "avg_realized_slippage_krw": _avg(slippage_krw),
            "avg_realized_slippage_bps": _avg(slippage_bps),
            "completed_valid_profit_count": len(completed_profit_rates),
            "completed_valid_profit_avg": _avg(completed_profit_rates),
        },
    }


def _fallback_regression_count(rows: Iterable[dict[str, Any]]) -> int:
    tokens = ("fallback_scout", "fallback_main", "fallback_single", "allow_fallback", "split-entry")
    return sum(1 for row in rows if any(token in _text_blob(row) for token in tokens))


def build_legacy_gatekeeper_summary(
    events: list[dict[str, Any]],
    *,
    since: time | None,
    until: time | None,
    label: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    window_rows = [row for row in events if _pipeline(row) == ENTRY_PIPELINE and _in_window(row, since, until)]
    holding_rows = [row for row in events if _pipeline(row) == HOLDING_PIPELINE and _in_window(row, since, until)]
    gatekeeper_decisions = [row for row in window_rows if _stage(row) in GATEKEEPER_DECISION_STAGES]
    gatekeeper_fast_reuse_events = [row for row in window_rows if _stage(row) == "gatekeeper_fast_reuse"]
    gatekeeper_bypass_events = [row for row in window_rows if _stage(row) == "gatekeeper_fast_reuse_bypass"]
    budget_pass_events = [row for row in window_rows if _stage(row) == "budget_pass"]
    submitted_events = [row for row in window_rows if _stage(row) == "order_bundle_submitted"]
    latency_block_events = [row for row in window_rows if _stage(row) == "latency_block"]
    latency_pass_events = [row for row in window_rows if _stage(row) == "latency_pass"]
    ai_confirmed_events = [row for row in window_rows if _stage(row) == "ai_confirmed"]
    entry_armed_events = [row for row in window_rows if _stage(row) in ENTRY_ARMED_STAGES]

    gatekeeper_eval_ms: list[float] = []
    gatekeeper_model_call_ms: list[float] = []
    gatekeeper_total_internal_ms: list[float] = []
    gatekeeper_action_ages: list[float] = []
    gatekeeper_allow_ages: list[float] = []
    gatekeeper_cache_modes: Counter[str] = Counter()
    gatekeeper_reuse_blockers: Counter[str] = Counter()
    gatekeeper_sig_deltas: Counter[str] = Counter()
    latency_reason_counts: Counter[str] = Counter()
    latency_danger_reason_counts: Counter[str] = Counter()
    quote_fresh_latency_blocks = 0
    quote_fresh_latency_passes = 0

    for row in gatekeeper_decisions:
        gatekeeper_cache_modes[str(_field(row, "gatekeeper_cache") or "miss")] += 1
        for source, container in (
            (_field(row, "gatekeeper_eval_ms"), gatekeeper_eval_ms),
            (_field(row, "gatekeeper_model_call_ms"), gatekeeper_model_call_ms),
            (_field(row, "gatekeeper_total_internal_ms"), gatekeeper_total_internal_ms),
        ):
            parsed = _safe_float(source)
            if parsed is not None:
                container.append(parsed)

    for row in gatekeeper_bypass_events:
        for code in _csv_counter(_field(row, "reason_codes")).keys():
            gatekeeper_reuse_blockers[_friendly_reuse_reason(code)] += 1
        _count_sig_delta_fields(gatekeeper_sig_deltas, _field(row, "sig_delta"))
        parsed_action_age = _safe_float(_field(row, "action_age_sec"))
        if parsed_action_age is not None:
            gatekeeper_action_ages.append(parsed_action_age)
        parsed_allow_age = _safe_float(_field(row, "allow_entry_age_sec"))
        if parsed_allow_age is not None:
            gatekeeper_allow_ages.append(parsed_allow_age)

    for row in latency_block_events:
        reason = str(_field(row, "reason") or "-")
        latency_reason_counts[reason] += 1
        latency_danger_reason_counts.update(_csv_counter(_field(row, "latency_danger_reasons", "danger_reasons")))
        if str(_field(row, "quote_stale") or "").strip().lower() in {"false", "0", "no"}:
            quote_fresh_latency_blocks += 1

    for row in latency_pass_events:
        if str(_field(row, "quote_stale") or "").strip().lower() in {"false", "0", "no"}:
            quote_fresh_latency_passes += 1

    full_fill_events, partial_fill_events = _fill_counts(holding_rows)
    gatekeeper_fast_reuse_ratio = _percent_point(
        _ratio(gatekeeper_cache_modes.get("fast_reuse", 0), len(gatekeeper_decisions))
    )
    metrics = {
        "ai_confirmed_events": len(ai_confirmed_events),
        "entry_armed_events": len(entry_armed_events),
        "budget_pass_events": len(budget_pass_events),
        "order_bundle_submitted_events": len(submitted_events),
        "budget_pass_to_submitted_rate": _percent_point(_ratio(len(submitted_events), len(budget_pass_events))),
        "latency_block_events": len(latency_block_events),
        "latency_pass_events": len(latency_pass_events),
        "latency_state_danger_events": int(latency_reason_counts.get("latency_state_danger", 0)),
        "quote_fresh_latency_blocks": quote_fresh_latency_blocks,
        "quote_fresh_latency_passes": quote_fresh_latency_passes,
        "quote_fresh_latency_pass_rate": _percent_point(
            _ratio(quote_fresh_latency_passes, quote_fresh_latency_passes + quote_fresh_latency_blocks)
        ),
        "gatekeeper_decisions": len(gatekeeper_decisions),
        "gatekeeper_fast_reuse_stage_events": len(gatekeeper_fast_reuse_events),
        "gatekeeper_fast_reuse_ratio": gatekeeper_fast_reuse_ratio,
        "gatekeeper_eval_ms_p95": _percentile(gatekeeper_eval_ms, 95),
        "gatekeeper_model_call_ms_p95": _percentile(gatekeeper_model_call_ms, 95),
        "gatekeeper_total_internal_ms_p95": _percentile(gatekeeper_total_internal_ms, 95),
        "gatekeeper_bypass_evaluation_samples": len(gatekeeper_bypass_events),
        "gatekeeper_action_age_p95": _percentile(gatekeeper_action_ages, 95),
        "gatekeeper_allow_entry_age_p95": _percentile(gatekeeper_allow_ages, 95),
        "full_fill_events": full_fill_events,
        "partial_fill_events": partial_fill_events,
    }
    smoke_status = (
        "observed"
        if metrics["gatekeeper_decisions"] > 0
        or metrics["gatekeeper_fast_reuse_stage_events"] > 0
        or metrics["gatekeeper_bypass_evaluation_samples"] > 0
        else "missing"
    )
    return {
        "schema_version": 2,
        "diagnostic_section": "legacy_gatekeeper_fast_reuse",
        "runtime_policy": "standby_diagnostic_report_only",
        "label": label,
        "window": {"since": since.isoformat() if since else None, "until": until.isoformat() if until else None},
        "bundle_metadata": metadata or {},
        "metrics": metrics,
        "breakdowns": {
            "latency_reason_breakdown": [{"label": key, "count": value} for key, value in latency_reason_counts.most_common()],
            "latency_danger_reason_breakdown": [
                {"label": key, "count": value} for key, value in latency_danger_reason_counts.most_common()
            ],
            "gatekeeper_reuse_blockers": [
                {"label": key, "count": value} for key, value in gatekeeper_reuse_blockers.most_common()
            ],
            "gatekeeper_sig_deltas": [{"label": key, "count": value} for key, value in gatekeeper_sig_deltas.most_common()],
        },
        "judgment": {
            "smoke_status": smoke_status,
            "directional_ready": bool(metrics["budget_pass_events"] >= 30 or metrics["gatekeeper_decisions"] >= 10),
            "why": (
                "legacy gatekeeper_fast_reuse/entry latency compatibility summary. "
                "Use as diagnostic evidence only; do not promote live entry logic from this section alone."
            ),
        },
    }


def _split_canary_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    applied = [row for row in rows if _canary_applied(row) is True]
    baseline = [row for row in rows if _canary_applied(row) is False]
    return applied, baseline


def _entry_rate_parts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    budget_pass = sum(1 for row in rows if _stage(row) == "budget_pass")
    submitted = sum(1 for row in rows if _stage(row) == "order_bundle_submitted")
    latency_blocks = [row for row in rows if _stage(row) == "latency_block"]
    danger = [
        row
        for row in latency_blocks
        if str(_field(row, "reason") or "") == "latency_state_danger"
        or str(_field(row, "latency_state") or "").upper() == "DANGER"
    ]
    return {
        "budget_pass": budget_pass,
        "submitted": submitted,
        "budget_pass_to_submitted_rate": _ratio(submitted, budget_pass),
        "latency_blocks": len(latency_blocks),
        "latency_state_danger": len(danger),
        "latency_state_danger_share": _ratio(len(danger), budget_pass),
    }


def _signal_quality_quote_candidate(row: dict[str, Any]) -> bool:
    if _stage(row) != "latency_block":
        return False
    if str(_field(row, "quote_stale") or "").strip().lower() == "true":
        return False
    reasons = set(_csv_counter(_field(row, "latency_danger_reasons", "danger_reasons")).keys())
    quote_reasons = {"other_danger", "ws_age_too_high", "ws_jitter_too_high", "spread_too_wide"}
    if not reasons or not reasons.issubset(quote_reasons):
        return False
    ai_score = _safe_float(_field(row, "ai_score"))
    latest_strength = _safe_float(_field(row, "latest_strength"))
    buy_pressure = _safe_float(_field(row, "buy_pressure_10t"))
    ws_age = _safe_float(_field(row, "ws_age_ms"))
    ws_jitter = _safe_float(_field(row, "ws_jitter_ms"))
    spread = _safe_float(_field(row, "spread_ratio"))
    return bool(
        ai_score is not None
        and latest_strength is not None
        and buy_pressure is not None
        and ws_age is not None
        and ws_jitter is not None
        and spread is not None
        and ai_score >= SIGNAL_QUALITY_QUOTE_MIN_SIGNAL
        and latest_strength >= SIGNAL_QUALITY_QUOTE_MIN_STRENGTH
        and buy_pressure >= SIGNAL_QUALITY_QUOTE_MIN_BUY_PRESSURE
        and ws_age <= SIGNAL_QUALITY_QUOTE_MAX_WS_AGE_MS
        and ws_jitter <= SIGNAL_QUALITY_QUOTE_MAX_WS_JITTER_MS
        and spread <= SIGNAL_QUALITY_QUOTE_MAX_SPREAD_RATIO
    )


def build_entry_summary(
    events: list[dict[str, Any]],
    *,
    since: time | None,
    until: time | None,
    label: str,
    shadow_diff_status: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    window_rows = [row for row in events if _pipeline(row) == ENTRY_PIPELINE and _in_window(row, since, until)]
    holding_rows = [row for row in events if _pipeline(row) == HOLDING_PIPELINE and _in_window(row, since, until)]
    budget_pass_events = sum(1 for row in window_rows if _stage(row) == "budget_pass")
    submitted_events = sum(1 for row in window_rows if _stage(row) == "order_bundle_submitted")
    latency_blocks = [row for row in window_rows if _stage(row) == "latency_block"]
    latency_state_danger = [
        row
        for row in latency_blocks
        if str(_field(row, "reason") or "") == "latency_state_danger"
        or str(_field(row, "latency_state") or "").upper() == "DANGER"
    ]
    reason_breakdown: Counter[str] = Counter()
    danger_reason_breakdown: Counter[str] = Counter()
    for row in latency_blocks:
        reason = str(_field(row, "reason") or "unknown")
        reason_breakdown[reason] += 1
        danger_reason_breakdown.update(_csv_counter(_field(row, "latency_danger_reasons", "danger_reasons")))

    applied_rows, baseline_rows = _split_canary_rows(window_rows)
    applied_parts = _entry_rate_parts(applied_rows)
    baseline_parts = _entry_rate_parts(baseline_rows)
    full_fill_events, partial_fill_events = _fill_counts(holding_rows)
    submitted_to_fill_rate = _ratio(full_fill_events + partial_fill_events, submitted_events)
    signal_quality_quote_candidates = [row for row in latency_blocks if _signal_quality_quote_candidate(row)]
    orderbook_stability = _orderbook_stability_summary(
        window_rows,
        holding_rows,
        [row for row in window_rows if _stage(row) == "order_bundle_submitted"],
        latency_state_danger,
    )
    latency_entry_price_guard = _latency_entry_price_guard_summary(window_rows, holding_rows)

    baseline_samples = baseline_parts["budget_pass"]
    hard_allowed = (
        submitted_events >= ENTRY_SUBMITTED_MIN
        and baseline_samples >= ENTRY_BASELINE_N_MIN
        and shadow_diff_status in {"resolved", "available"}
    )
    direction_reasons = []
    if submitted_events < ENTRY_SUBMITTED_MIN:
        direction_reasons.append(f"submitted_orders<{ENTRY_SUBMITTED_MIN}")
    if baseline_samples < ENTRY_BASELINE_N_MIN:
        direction_reasons.append(f"baseline<{ENTRY_BASELINE_N_MIN}")
    if shadow_diff_status not in {"resolved", "available"}:
        direction_reasons.append("ShadowDiff0428_unresolved")

    applied_rate = applied_parts["budget_pass_to_submitted_rate"]
    baseline_rate = baseline_parts["budget_pass_to_submitted_rate"]
    applied_danger = applied_parts["latency_state_danger_share"]
    baseline_danger = baseline_parts["latency_state_danger_share"]
    entry_arrival_primary_pass = (
        applied_rate is not None and baseline_rate is not None and (applied_rate - baseline_rate) >= 0.01
    )
    entry_arrival_secondary_pass = (
        applied_danger is not None and baseline_danger is not None and (baseline_danger - applied_danger) >= 0.05
    )
    entry_fill_quality_non_worse = True if submitted_to_fill_rate is not None else False
    composite_no_recovery = hard_allowed and not entry_arrival_primary_pass

    return {
        "schema_version": 1,
        "axis": "latency_quote_fresh_composite",
        "label": label,
        "window": {"since": since.isoformat() if since else None, "until": until.isoformat() if until else None},
        "bundle_metadata": metadata or {},
        "budget_pass_events": budget_pass_events,
        "order_bundle_submitted_events": submitted_events,
        "submitted_orders": submitted_events,
        "budget_pass_to_submitted_rate": _percent_point(_ratio(submitted_events, budget_pass_events)),
        "latency_block_events": len(latency_blocks),
        "latency_state_danger_events": len(latency_state_danger),
        "latency_state_danger_share": _percent_point(_ratio(len(latency_state_danger), budget_pass_events)),
        "latency_reason_breakdown": dict(reason_breakdown),
        "latency_danger_reason_breakdown": dict(danger_reason_breakdown),
        "quote_fresh_composite_canary_applied_true": len(applied_rows),
        "quote_fresh_composite_canary_applied_false": len(baseline_rows),
        "canary_applied_budget_pass_to_submitted_rate": _percent_point(applied_rate),
        "baseline_budget_pass_to_submitted_rate": _percent_point(baseline_rate),
        "canary_applied_latency_state_danger_share": _percent_point(applied_danger),
        "baseline_latency_state_danger_share": _percent_point(baseline_danger),
        "full_fill_events": full_fill_events,
        "partial_fill_events": partial_fill_events,
        "submitted_to_fill_rate": _percent_point(submitted_to_fill_rate),
        "fallback_regression_count": _fallback_regression_count(window_rows + holding_rows),
        "signal_quality_quote_composite_candidate_events": len(signal_quality_quote_candidates),
        "orderbook_stability": orderbook_stability,
        "latency_entry_price_guard": latency_entry_price_guard,
        "signal_quality_quote_composite_candidate_thresholds": {
            "min_signal": SIGNAL_QUALITY_QUOTE_MIN_SIGNAL,
            "min_strength": SIGNAL_QUALITY_QUOTE_MIN_STRENGTH,
            "min_buy_pressure": SIGNAL_QUALITY_QUOTE_MIN_BUY_PRESSURE,
            "max_ws_age_ms": SIGNAL_QUALITY_QUOTE_MAX_WS_AGE_MS,
            "max_ws_jitter_ms": SIGNAL_QUALITY_QUOTE_MAX_WS_JITTER_MS,
            "max_spread_ratio": SIGNAL_QUALITY_QUOTE_MAX_SPREAD_RATIO,
        },
        "shadow_diff_status": shadow_diff_status,
        "hard_pass_fail_allowed": hard_allowed,
        "direction_only_reason": ", ".join(direction_reasons) if direction_reasons else "",
        "entry_arrival_primary_pass": bool(entry_arrival_primary_pass),
        "entry_arrival_secondary_pass": bool(entry_arrival_secondary_pass),
        "entry_fill_quality_non_worse": bool(entry_fill_quality_non_worse),
        "composite_no_recovery": bool(composite_no_recovery),
    }


def _exit_rule(row: dict[str, Any]) -> str:
    return str(_field(row, "exit_rule", "exit_rule_candidate", "last_exit_rule") or row.get("exit_rule") or "").strip()


def _completed_valid_profit_rates(rows: Iterable[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for row in rows:
        blob = _text_blob(row)
        status = str(_field(row, "status", "trade_status") or "").upper()
        profit = _safe_float(_field(row, "profit_rate", "realized_profit_rate"))
        if profit is None:
            continue
        if status == "COMPLETED" or "completed" in blob or _stage(row) in {"exit_signal", "sell_completed"}:
            values.append(profit)
    return values


def _post_sell_metric(row: dict[str, Any], horizon: str, name: str) -> Any:
    metrics = row.get(f"metrics_{horizon}")
    if isinstance(metrics, dict):
        return metrics.get(name)
    return None


def _same_symbol_reentry_loss_count(candidates: list[dict[str, Any]], evaluations: list[dict[str, Any]]) -> int:
    rows = candidates + evaluations
    count = 0
    for row in rows:
        same_symbol = _truthy(row.get("same_symbol_reentry_loss") or row.get("same_symbol_soft_stop_cooldown_would_block"))
        profit = _safe_float(row.get("profit_rate"))
        if same_symbol is True and profit is not None and profit < 0:
            count += 1
    return count


def build_soft_stop_summary(
    events: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    evaluations: list[dict[str, Any]],
    *,
    since: time | None,
    until: time | None,
    label: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    holding_rows = [row for row in events if _pipeline(row) == HOLDING_PIPELINE and _in_window(row, since, until)]
    grace_events = [row for row in holding_rows if _stage(row) == "soft_stop_micro_grace"]
    extension_used_events = [row for row in grace_events if _truthy(_field(row, "extension_used")) is True]
    soft_stop_events = [row for row in holding_rows if _exit_rule(row) == "scalp_soft_stop_pct" or "scalp_soft_stop_pct" in _text_blob(row)]
    hard_stop_events = [
        row
        for row in holding_rows
        if _exit_rule(row) in {"scalp_hard_stop_pct", "scalp_preset_hard_stop_pct", "protect_hard_stop"}
        or "hard_stop" in _text_blob(row)
    ]
    emergency_events = []
    for row in grace_events:
        profit = _safe_float(_field(row, "profit_rate"))
        emergency_pct = _safe_float(_field(row, "emergency_pct"))
        if profit is not None and emergency_pct is not None and profit <= emergency_pct:
            emergency_events.append(row)
    completed_rates = _completed_valid_profit_rates(holding_rows)
    full_fill_events, partial_fill_events = _fill_counts(holding_rows)

    soft_stop_eval_rows = [row for row in evaluations if str(row.get("exit_rule") or "") == "scalp_soft_stop_pct"]
    rebound_sell = sum(1 for row in soft_stop_eval_rows if _truthy(_post_sell_metric(row, "10m", "rebound_above_sell")) is True)
    rebound_buy = sum(1 for row in soft_stop_eval_rows if _truthy(_post_sell_metric(row, "10m", "rebound_above_buy")) is True)
    mfe_ge_0_5 = sum(1 for row in soft_stop_eval_rows if (_safe_float(_post_sell_metric(row, "10m", "mfe_pct")) or -999.0) >= 0.5)
    mfe_ge_1_0 = sum(1 for row in soft_stop_eval_rows if (_safe_float(_post_sell_metric(row, "10m", "mfe_pct")) or -999.0) >= 1.0)
    same_symbol_losses = _same_symbol_reentry_loss_count(candidates, evaluations)

    hard_allowed = len(grace_events) >= SOFT_STOP_GRACE_MIN or len(completed_rates) >= VALID_COMPLETED_MIN
    direction_reasons = []
    if len(grace_events) < SOFT_STOP_GRACE_MIN:
        direction_reasons.append(f"soft_stop_micro_grace_events<{SOFT_STOP_GRACE_MIN}")
    if len(completed_rates) < VALID_COMPLETED_MIN:
        direction_reasons.append(f"completed_valid_trades<{VALID_COMPLETED_MIN}")

    avg_profit = round(sum(completed_rates) / len(completed_rates), 6) if completed_rates else None
    soft_stop_loss_tail_improved = bool(hard_allowed and avg_profit is not None and avg_profit >= -1.5)
    hard_or_emergency_worse = len(hard_stop_events) > 0 or len(emergency_events) > 0
    same_symbol_reentry_worse = same_symbol_losses > 0
    if not hard_allowed:
        recommended_action = "direction_only_collect_more_samples"
    elif hard_or_emergency_worse or same_symbol_reentry_worse:
        recommended_action = "review_or_reduce_micro_grace"
    elif soft_stop_loss_tail_improved:
        recommended_action = "keep_micro_grace"
    else:
        recommended_action = "no_improvement_replace_axis"

    return {
        "schema_version": 1,
        "axis": "soft_stop_micro_grace",
        "label": label,
        "window": {"since": since.isoformat() if since else None, "until": until.isoformat() if until else None},
        "bundle_metadata": metadata or {},
        "soft_stop_micro_grace_events": len(grace_events),
        "soft_stop_micro_grace_extension_used_events": len(extension_used_events),
        "scalp_soft_stop_pct_events": len(soft_stop_events),
        "scalp_hard_stop_pct_events": len(hard_stop_events),
        "emergency_stop_events": len(emergency_events),
        "completed_valid_trades": len(completed_rates),
        "completed_valid_profit_sum": round(sum(completed_rates), 6),
        "completed_valid_profit_avg": avg_profit,
        "full_fill_events": full_fill_events,
        "partial_fill_events": partial_fill_events,
        "same_symbol_reentry_loss_count": same_symbol_losses,
        "fallback_regression_count": _fallback_regression_count(holding_rows),
        "post_sell_soft_stop_rebound_above_sell_10m": rebound_sell,
        "post_sell_soft_stop_rebound_above_buy_10m": rebound_buy,
        "mfe_ge_0_5": mfe_ge_0_5,
        "mfe_ge_1_0": mfe_ge_1_0,
        "hard_pass_fail_allowed": hard_allowed,
        "direction_only_reason": ", ".join(direction_reasons) if direction_reasons else "",
        "soft_stop_loss_tail_improved": soft_stop_loss_tail_improved,
        "hard_stop_or_emergency_worse": hard_or_emergency_worse,
        "same_symbol_reentry_worse": same_symbol_reentry_worse,
        "recommended_action": recommended_action,
    }


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _render_entry_md(summary: dict[str, Any]) -> str:
    orderbook = summary.get("orderbook_stability") or {}
    price_guard = summary.get("latency_entry_price_guard") or {}
    three_tick_guard = price_guard.get("three_tick_guard") or {}
    metadata = summary.get("bundle_metadata") or {}
    return "\n".join(
        [
            f"# Entry Quote Fresh Composite Summary ({summary['label']})",
            "",
            "## Bundle",
            f"- bundle_dir: `{metadata.get('bundle_dir', '-')}`",
            f"- target_date: `{metadata.get('target_date', '-')}`",
            f"- manifest_generated_at: `{metadata.get('manifest_generated_at', '-')}`",
            f"- pipeline_event_rows_loaded: `{metadata.get('pipeline_event_rows_loaded', 0)}`",
            "",
            "## 판정",
            f"- hard_pass_fail_allowed: `{summary['hard_pass_fail_allowed']}`",
            f"- direction_only_reason: `{summary['direction_only_reason'] or '-'}`",
            f"- entry_arrival_primary_pass: `{summary['entry_arrival_primary_pass']}`",
            f"- entry_arrival_secondary_pass: `{summary['entry_arrival_secondary_pass']}`",
            f"- entry_fill_quality_non_worse: `{summary['entry_fill_quality_non_worse']}`",
            f"- composite_no_recovery: `{summary['composite_no_recovery']}`",
            "",
            "## 근거",
            f"- budget_pass_events: `{summary['budget_pass_events']}`",
            f"- order_bundle_submitted_events: `{summary['order_bundle_submitted_events']}`",
            f"- budget_pass_to_submitted_rate: `{summary['budget_pass_to_submitted_rate']}`%",
            f"- latency_state_danger_events/share: `{summary['latency_state_danger_events']}` / `{summary['latency_state_danger_share']}`%",
            f"- full/partial fill: `{summary['full_fill_events']}` / `{summary['partial_fill_events']}`",
            f"- fallback_regression_count: `{summary['fallback_regression_count']}`",
            f"- signal_quality_quote_composite_candidate_events: `{summary['signal_quality_quote_composite_candidate_events']}`",
            f"- latency_entry_price_guard_breakdown: `{price_guard.get('submitted_guard_breakdown', {})}`",
            f"- latency_3tick_guard submitted/fill/fill_rate: `{three_tick_guard.get('submitted_count', 0)}` / `{three_tick_guard.get('fill_count', 0)}` / `{three_tick_guard.get('fill_rate')}`%",
            f"- latency_3tick_guard realized_slippage krw/bps: `{three_tick_guard.get('avg_realized_slippage_krw')}` / `{three_tick_guard.get('avg_realized_slippage_bps')}`",
            f"- latency_3tick_guard completed_valid_profit count/avg: `{three_tick_guard.get('completed_valid_profit_count', 0)}` / `{three_tick_guard.get('completed_valid_profit_avg')}`",
            f"- orderbook_stability_observed_count: `{orderbook.get('orderbook_stability_observed_count', 0)}`",
            f"- unstable_quote_observed_count/share: `{orderbook.get('unstable_quote_observed_count', 0)}` / `{orderbook.get('unstable_quote_share')}`%",
            f"- unstable_reason_breakdown: `{orderbook.get('unstable_reason_breakdown', {})}`",
            f"- unstable_vs_submitted: `{orderbook.get('unstable_vs_submitted', {})}`",
            f"- unstable_vs_fill: `{orderbook.get('unstable_vs_fill', {})}`",
            f"- unstable_vs_latency_danger: `{orderbook.get('unstable_vs_latency_danger', {})}`",
            f"- shadow_diff_status: `{summary['shadow_diff_status']}`",
            "",
            "## 다음 액션",
            "- hard pass/fail 전제가 닫히지 않으면 direction-only로만 유지/종료를 판단한다.",
        ]
    )


def _render_soft_stop_md(summary: dict[str, Any]) -> str:
    metadata = summary.get("bundle_metadata") or {}
    return "\n".join(
        [
            f"# Soft Stop Micro Grace Summary ({summary['label']})",
            "",
            "## Bundle",
            f"- bundle_dir: `{metadata.get('bundle_dir', '-')}`",
            f"- target_date: `{metadata.get('target_date', '-')}`",
            f"- manifest_generated_at: `{metadata.get('manifest_generated_at', '-')}`",
            f"- pipeline_event_rows_loaded: `{metadata.get('pipeline_event_rows_loaded', 0)}`",
            "",
            "## 판정",
            f"- hard_pass_fail_allowed: `{summary['hard_pass_fail_allowed']}`",
            f"- direction_only_reason: `{summary['direction_only_reason'] or '-'}`",
            f"- recommended_action: `{summary['recommended_action']}`",
            "",
            "## 근거",
            f"- soft_stop_micro_grace_events: `{summary['soft_stop_micro_grace_events']}`",
            f"- soft_stop_micro_grace_extension_used_events: `{summary['soft_stop_micro_grace_extension_used_events']}`",
            f"- scalp_soft_stop_pct_events: `{summary['scalp_soft_stop_pct_events']}`",
            f"- scalp_hard_stop_pct_events/emergency_stop_events: `{summary['scalp_hard_stop_pct_events']}` / `{summary['emergency_stop_events']}`",
            f"- completed_valid_trades/profit_avg: `{summary['completed_valid_trades']}` / `{summary['completed_valid_profit_avg']}`",
            f"- post_sell rebound sell/buy 10m: `{summary['post_sell_soft_stop_rebound_above_sell_10m']}` / `{summary['post_sell_soft_stop_rebound_above_buy_10m']}`",
            f"- mfe_ge_0_5 / mfe_ge_1_0: `{summary['mfe_ge_0_5']}` / `{summary['mfe_ge_1_0']}`",
            "",
            "## 다음 액션",
            "- `recommended_action`에 따라 유지, 축소, 교체 중 하나로 닫는다.",
        ]
    )


def _render_combined_md(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Live Canary Combined Summary ({summary['label']})",
            "",
            "## 판정",
            f"- entry_hard_pass_fail_allowed: `{summary['entry']['hard_pass_fail_allowed']}`",
            f"- soft_stop_hard_pass_fail_allowed: `{summary['soft_stop']['hard_pass_fail_allowed']}`",
            "",
            "## 근거",
            f"- entry submitted/fill: `{summary['entry']['order_bundle_submitted_events']}` / `{summary['entry']['full_fill_events'] + summary['entry']['partial_fill_events']}`",
            f"- soft_stop grace/completed: `{summary['soft_stop']['soft_stop_micro_grace_events']}` / `{summary['soft_stop']['completed_valid_trades']}`",
            f"- legacy gatekeeper smoke_status: `{summary['legacy_gatekeeper']['judgment']['smoke_status']}`",
            "",
            "## 다음 액션",
            "- 이 bundle은 standby diagnostic/report-only 입력이다. live threshold/order/exit 판단을 직접 변경하지 않는다.",
        ]
    )


def _render_legacy_gatekeeper_md(summary: dict[str, Any]) -> str:
    metrics = summary.get("metrics") or {}
    breakdowns = summary.get("breakdowns") or {}

    def _top_lines(rows: list[dict[str, Any]], *, limit: int = 5) -> list[str]:
        lines = [f"- {row.get('label')}: {row.get('count')}" for row in rows[:limit]]
        return lines or ["- -"]

    return "\n".join(
        [
            f"# Legacy Gatekeeper Fast Reuse Summary ({summary['label']})",
            "",
            "## 판정",
            "- runtime_policy: `standby_diagnostic_report_only`",
            f"- smoke_status: `{summary['judgment']['smoke_status']}`",
            f"- directional_ready: `{summary['judgment']['directional_ready']}`",
            "",
            "## 근거",
            f"- budget_pass_events: `{metrics.get('budget_pass_events', 0)}`",
            f"- order_bundle_submitted_events: `{metrics.get('order_bundle_submitted_events', 0)}`",
            f"- budget_pass_to_submitted_rate: `{metrics.get('budget_pass_to_submitted_rate')}`%",
            f"- latency_block_events: `{metrics.get('latency_block_events', 0)}`",
            f"- latency_state_danger_events: `{metrics.get('latency_state_danger_events', 0)}`",
            f"- quote_fresh_latency_pass_rate: `{metrics.get('quote_fresh_latency_pass_rate')}`%",
            f"- gatekeeper_decisions: `{metrics.get('gatekeeper_decisions', 0)}`",
            f"- gatekeeper_fast_reuse_stage_events: `{metrics.get('gatekeeper_fast_reuse_stage_events', 0)}`",
            f"- gatekeeper_fast_reuse_ratio: `{metrics.get('gatekeeper_fast_reuse_ratio')}`%",
            f"- gatekeeper_eval_ms_p95: `{metrics.get('gatekeeper_eval_ms_p95')}`ms",
            f"- full/partial fill: `{metrics.get('full_fill_events', 0)}` / `{metrics.get('partial_fill_events', 0)}`",
            "",
            "## Latency Reasons",
            *_top_lines(breakdowns.get("latency_reason_breakdown") or []),
            "",
            "## Danger Reasons",
            *_top_lines(breakdowns.get("latency_danger_reason_breakdown") or []),
            "",
            "## Reuse Blockers",
            *_top_lines(breakdowns.get("gatekeeper_reuse_blockers") or []),
            "",
            "## 다음 액션",
            "- legacy 지표는 제출병목 보조 진단으로만 사용하고, submitted/full/partial 회복 없이 live 후보로 승격하지 않는다.",
        ]
    )


def run_analysis(
    bundle_dir: Path,
    *,
    since: str | None,
    until: str | None,
    cumulative_since: str | None,
    label: str,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    if cumulative_since and since:
        raise ValueError("--since and --cumulative-since cannot be used together")
    manifest = _load_manifest(bundle_dir)
    target_date = str(manifest.get("target_date") or "").strip() or None
    since_time = _parse_time(cumulative_since or since)
    until_time = _parse_time(until or manifest.get("evidence_cutoff"))
    events = _load_pipeline_events(bundle_dir, since_time, until_time, target_date)
    candidates, evaluations = _load_post_sell_rows(bundle_dir, since_time, until_time, target_date)
    shadow_status = _load_shadow_diff_status(bundle_dir)
    metadata = {
        "bundle_dir": str(bundle_dir),
        "target_date": manifest.get("target_date"),
        "manifest_generated_at": manifest.get("generated_at"),
        "pipeline_event_rows_loaded": len(events),
    }

    entry = build_entry_summary(
        events,
        since=since_time,
        until=until_time,
        label=label,
        shadow_diff_status=shadow_status,
        metadata=metadata,
    )
    soft_stop = build_soft_stop_summary(
        events,
        candidates,
        evaluations,
        since=since_time,
        until=until_time,
        label=label,
        metadata=metadata,
    )
    legacy_gatekeeper = build_legacy_gatekeeper_summary(
        events,
        since=since_time,
        until=until_time,
        label=label,
        metadata=metadata,
    )
    combined = {
        "schema_version": 2,
        "label": label,
        "bundle_dir": str(bundle_dir),
        "target_date": manifest.get("target_date"),
        "window": {"since": since_time.isoformat() if since_time else None, "until": until_time.isoformat() if until_time else None},
        "runtime_policy": "standby_diagnostic_report_only",
        "diagnostic_sections": [
            "entry_quote_fresh_composite",
            "soft_stop_micro_grace",
            "legacy_gatekeeper_fast_reuse",
            "entry_latency_offline",
        ],
        "entry": entry,
        "soft_stop": soft_stop,
        "legacy_gatekeeper": legacy_gatekeeper,
    }

    results_dir = output_dir or (bundle_dir / "results")
    _write_json(results_dir / f"entry_quote_fresh_composite_summary_{label}.json", entry)
    (results_dir / f"entry_quote_fresh_composite_summary_{label}.md").write_text(_render_entry_md(entry), encoding="utf-8")
    _write_json(results_dir / f"soft_stop_micro_grace_summary_{label}.json", soft_stop)
    (results_dir / f"soft_stop_micro_grace_summary_{label}.md").write_text(_render_soft_stop_md(soft_stop), encoding="utf-8")
    _write_json(results_dir / f"gatekeeper_fast_reuse_summary_{label}.json", legacy_gatekeeper)
    (results_dir / f"gatekeeper_fast_reuse_summary_{label}.md").write_text(
        _render_legacy_gatekeeper_md(legacy_gatekeeper),
        encoding="utf-8",
    )
    _write_json(results_dir / f"entry_latency_offline_summary_{label}.json", legacy_gatekeeper)
    (results_dir / f"entry_latency_offline_summary_{label}.md").write_text(
        _render_legacy_gatekeeper_md(legacy_gatekeeper),
        encoding="utf-8",
    )
    _write_json(results_dir / f"live_canary_combined_summary_{label}.json", combined)
    (results_dir / f"live_canary_combined_summary_{label}.md").write_text(_render_combined_md(combined), encoding="utf-8")
    return combined


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze an offline live canary bundle")
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--since", default=None, help="HH:MM:SS")
    parser.add_argument("--until", default=None, help="HH:MM:SS")
    parser.add_argument("--cumulative-since", default=None, help="HH:MM:SS")
    parser.add_argument("--label", required=True)
    parser.add_argument("--output-dir", type=Path, default=None, help="Optional directory for summary outputs")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    combined = run_analysis(
        args.bundle_dir,
        since=args.since,
        until=args.until,
        cumulative_since=args.cumulative_since,
        label=args.label,
        output_dir=args.output_dir,
    )
    results_dir = args.output_dir or (args.bundle_dir / "results")
    print(f"wrote live canary summaries: {results_dir}")
    print(json.dumps({"label": combined["label"], "window": combined["window"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
