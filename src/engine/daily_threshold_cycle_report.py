"""Daily threshold cycle report for post-close recommendation and next-preopen apply."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from src.utils.constants import DATA_DIR, POSTGRES_URL, TRADING_RULES


REPORT_DIR = DATA_DIR / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
THRESHOLD_CYCLE_SCHEMA_VERSION = 1
THRESHOLD_CYCLE_DIR = DATA_DIR / "threshold_cycle"
TARGET_STAGES = {
    "budget_pass",
    "order_bundle_submitted",
    "latency_pass",
    "bad_entry_block_observed",
    "reversal_add_candidate",
    "reversal_add_blocked_reason",
    "soft_stop_micro_grace",
    "pre_submit_price_guard_block",
}
RAW_PIPELINE_FALLBACK_MAX_BYTES = 64 * 1024 * 1024


@dataclass
class ThresholdCycleContext:
    warnings: list[str]


@dataclass
class PipelineLoadResult:
    rows: list[dict]
    meta: dict[str, Any]


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        result = float(value)
    except Exception:
        return default
    return result if math.isfinite(result) else default


def _safe_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def _percentile(values: list[float], pct: float, default: float = 0.0) -> float:
    cleaned = sorted(float(v) for v in values if v is not None and math.isfinite(float(v)))
    if not cleaned:
        return default
    if len(cleaned) == 1:
        return cleaned[0]
    rank = max(0, min(len(cleaned) - 1, math.ceil((pct / 100.0) * len(cleaned)) - 1))
    return cleaned[rank]


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _date_range(target_date: str, days: int) -> list[str]:
    end = datetime.strptime(target_date, "%Y-%m-%d").date()
    start = end - timedelta(days=max(0, days - 1))
    values: list[str] = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def report_path_for_date(target_date: str) -> Path:
    return REPORT_DIR / f"threshold_cycle_{target_date}.json"


def save_threshold_cycle_report(report: dict) -> Path:
    target_date = str(report.get("date") or date.today().isoformat())
    path = report_path_for_date(target_date)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    return path


def _import_sqlalchemy():
    from sqlalchemy import create_engine, text

    return create_engine, text


def _default_completed_rows_loader(start_date: str, end_date: str) -> list[dict]:
    create_engine, text = _import_sqlalchemy()
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    query = text(
        """
        SELECT
            rec_date,
            stock_code,
            stock_name,
            status,
            strategy,
            buy_qty,
            profit_rate
        FROM recommendation_history
        WHERE rec_date >= :start_date
          AND rec_date <= :end_date
          AND status = 'COMPLETED'
          AND profit_rate IS NOT NULL
        ORDER BY rec_date DESC, stock_code
        """
    )
    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(query, {"start_date": start_date, "end_date": end_date}).mappings().all()]


def _read_threshold_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            if str(payload.get("stage") or "") not in TARGET_STAGES:
                continue
            rows.append(payload)
    return rows


def _checkpoint_for_date(target_date: str) -> dict:
    path = THRESHOLD_CYCLE_DIR / "checkpoints" / f"{target_date}.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _partition_paths_for_date(target_date: str) -> list[Path]:
    root = THRESHOLD_CYCLE_DIR / f"date={target_date}"
    if not root.exists():
        return []
    return sorted(root.glob("family=*/part-*.jsonl"))


def _load_partitioned_pipeline_events(target_date: str) -> PipelineLoadResult | None:
    paths = _partition_paths_for_date(target_date)
    if not paths:
        return None
    rows: list[dict] = []
    read_bytes = 0
    for path in paths:
        try:
            read_bytes += path.stat().st_size
            rows.extend(_read_threshold_jsonl(path))
        except OSError:
            continue
    checkpoint = _checkpoint_for_date(target_date)
    return PipelineLoadResult(
        rows=rows,
        meta={
            "target_date": target_date,
            "data_source": "partitioned_compact",
            "partition_count": len(paths),
            "line_count": len(rows),
            "checkpoint_completed": bool(checkpoint.get("completed")) if checkpoint else None,
            "paused_reason": checkpoint.get("paused_reason") if checkpoint else None,
            "read_bytes_estimate": read_bytes,
            "warnings": [],
        },
    )


def _default_pipeline_load_result(target_date: str) -> PipelineLoadResult:
    partitioned = _load_partitioned_pipeline_events(target_date)
    if partitioned is not None:
        return partitioned

    compact_path = THRESHOLD_CYCLE_DIR / f"threshold_events_{target_date}.jsonl"
    if compact_path.exists():
        rows = _read_threshold_jsonl(compact_path)
        return PipelineLoadResult(
            rows=rows,
            meta={
                "target_date": target_date,
                "data_source": "legacy_compact",
                "partition_count": 0,
                "line_count": len(rows),
                "checkpoint_completed": None,
                "paused_reason": None,
                "read_bytes_estimate": compact_path.stat().st_size,
                "warnings": [],
            },
        )

    jsonl_path = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    if jsonl_path.exists() and jsonl_path.stat().st_size <= RAW_PIPELINE_FALLBACK_MAX_BYTES:
        rows: list[dict] = []
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(payload, dict):
                    continue
                if str(payload.get("stage") or "") not in TARGET_STAGES:
                    continue
                if payload.get("event_type") not in (None, "", "pipeline_event"):
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
        return PipelineLoadResult(
            rows=rows,
            meta={
                "target_date": target_date,
                "data_source": "small_raw_fallback",
                "partition_count": 0,
                "line_count": len(rows),
                "checkpoint_completed": None,
                "paused_reason": None,
                "read_bytes_estimate": jsonl_path.stat().st_size,
                "warnings": ["raw fallback used; compact partition missing"],
            },
        )
    warnings = []
    if jsonl_path.exists():
        warnings.append(f"raw fallback skipped: file exceeds {RAW_PIPELINE_FALLBACK_MAX_BYTES} bytes")
    return PipelineLoadResult(
        rows=[],
        meta={
            "target_date": target_date,
            "data_source": "none",
            "partition_count": 0,
            "line_count": 0,
            "checkpoint_completed": None,
            "paused_reason": None,
            "read_bytes_estimate": 0,
            "warnings": warnings,
        },
    )


def _default_pipeline_loader(target_date: str) -> list[dict]:
    return _default_pipeline_load_result(target_date).rows


def _extract_field_values(events: list[dict], stage: str, field_name: str) -> list[float]:
    values: list[float] = []
    for event in events:
        if str(event.get("stage") or "") != stage:
            continue
        fields = event.get("fields") or {}
        if not isinstance(fields, dict):
            continue
        value = _safe_float(fields.get(field_name), None)
        if value is not None:
            values.append(value)
    return values


def _stage_count(events: list[dict], stage: str) -> int:
    return sum(1 for event in events if str(event.get("stage") or "") == stage)


def _completed_summary(rows: list[dict]) -> dict:
    total = len(rows)
    losses = [row for row in rows if (_safe_float(row.get("profit_rate"), 0.0) or 0.0) < 0.0]
    return {
        "completed_valid": total,
        "loss_count": len(losses),
    }


def _build_mechanical_entry_family(events: list[dict]) -> dict:
    current = {
        "max_signal_score": float(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE", 75.0) or 75.0),
        "min_strength": float(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH", 110.0) or 110.0),
        "min_buy_pressure": float(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE", 50.0) or 50.0),
        "max_ws_age_ms": int(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_AGE_MS", 1200) or 1200),
        "max_ws_jitter_ms": int(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_JITTER_MS", 500) or 500),
        "max_spread_ratio": float(getattr(TRADING_RULES, "SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SPREAD_RATIO", 0.0085) or 0.0085),
    }
    budget_pass = _stage_count(events, "budget_pass")
    submitted = _stage_count(events, "order_bundle_submitted")
    strength = _extract_field_values(events, "budget_pass", "latest_strength")
    buy_pressure = _extract_field_values(events, "budget_pass", "buy_pressure_10t")
    ws_age = _extract_field_values(events, "budget_pass", "ws_age_ms")
    ws_jitter = _extract_field_values(events, "budget_pass", "ws_jitter_ms")
    spread = _extract_field_values(events, "budget_pass", "spread_ratio")
    signal_score = _extract_field_values(events, "budget_pass", "signal_score")

    sample_ready = budget_pass >= 500 and submitted >= 20
    recommended = {
        "max_signal_score": round(_clamp(_percentile(signal_score, 90, current["max_signal_score"]), 65.0, 85.0), 1),
        "min_strength": round(_clamp(_percentile(strength, 25, current["min_strength"]), 95.0, 130.0), 1),
        "min_buy_pressure": round(_clamp(_percentile(buy_pressure, 25, current["min_buy_pressure"]), 45.0, 70.0), 1),
        "max_ws_age_ms": int(round(_clamp(_percentile(ws_age, 90, current["max_ws_age_ms"]), 600.0, 1600.0))),
        "max_ws_jitter_ms": int(round(_clamp(_percentile(ws_jitter, 90, current["max_ws_jitter_ms"]), 200.0, 700.0))),
        "max_spread_ratio": round(_clamp(_percentile(spread, 90, current["max_spread_ratio"]), 0.0040, 0.0120), 4),
    }
    return {
        "family": "entry_mechanical_momentum",
        "stage": "entry",
        "sample": {"budget_pass": budget_pass, "submitted": submitted},
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "entry family는 same-day holding/exit live owner와 분리한다.",
            "budget_pass>=500, submitted>=20 미만이면 추천값은 shadow reference로만 사용한다.",
        ],
    }


def _build_pre_submit_guard_family(events: list[dict]) -> dict:
    current = {
        "max_below_bid_bps": int(getattr(TRADING_RULES, "SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS", 80) or 80),
    }
    values = _extract_field_values(events, "order_bundle_submitted", "price_below_bid_bps")
    if not values:
        values = _extract_field_values(events, "latency_pass", "price_below_bid_bps")
    sample_ready = len(values) >= 50
    recommended = {
        "max_below_bid_bps": int(round(_clamp(_percentile(values, 90, current["max_below_bid_bps"]), 60.0, 120.0))),
    }
    return {
        "family": "pre_submit_price_guard",
        "stage": "entry",
        "sample": {"price_below_bid_bps": len(values), "guard_block": _stage_count(events, "pre_submit_price_guard_block")},
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "실제 guard_block 표본이 0이면 분포 anchor만 사용한다.",
            "일일 변경폭은 +-10bps cap으로 본다.",
        ],
    }


def _build_bad_entry_family(events: list[dict]) -> dict:
    current = {
        "min_hold_sec": int(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_BLOCK_MIN_HOLD_SEC", 60) or 60),
        "min_loss_pct": float(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_BLOCK_MIN_LOSS_PCT", -0.70) or -0.70),
        "max_peak_profit_pct": float(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_BLOCK_MAX_PEAK_PROFIT_PCT", 0.20) or 0.20),
        "ai_score_limit": int(getattr(TRADING_RULES, "SCALP_BAD_ENTRY_BLOCK_AI_SCORE_LIMIT", 45) or 45),
    }
    observed = [event for event in events if str(event.get("stage") or "") == "bad_entry_block_observed"]
    hold_values = [_safe_float((event.get("fields") or {}).get("held_sec"), None) for event in observed]
    loss_values = [_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in observed]
    peak_values = [_safe_float((event.get("fields") or {}).get("peak_profit"), None) for event in observed]
    ai_values = [_safe_float((event.get("fields") or {}).get("ai_score"), None) for event in observed]
    hold_values = [v for v in hold_values if v is not None]
    loss_values = [v for v in loss_values if v is not None]
    peak_values = [v for v in peak_values if v is not None]
    ai_values = [v for v in ai_values if v is not None]
    sample_ready = len(observed) >= 30
    recommended = {
        "min_hold_sec": int(round(_clamp(_percentile(hold_values, 25, current["min_hold_sec"]), 30.0, 180.0))),
        "min_loss_pct": round(_clamp(_percentile(loss_values, 35, current["min_loss_pct"]), -1.5, -0.3), 2),
        "max_peak_profit_pct": round(_clamp(_percentile(peak_values, 75, current["max_peak_profit_pct"]), 0.05, 0.5), 2),
        "ai_score_limit": int(round(_clamp(_percentile(ai_values, 75, current["ai_score_limit"]), 30.0, 60.0))),
    }
    return {
        "family": "bad_entry_block",
        "stage": "holding_exit",
        "sample": {"observed": len(observed)},
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "today live block은 열지 않고 observe->postclose->next_preopen 순서만 허용한다.",
            "후행 soft_stop/hard_stop 연결이 불충분하면 추천값은 shadow 유지다.",
        ],
    }


def _build_reversal_add_family(events: list[dict]) -> dict:
    current = {
        "pnl_min": float(getattr(TRADING_RULES, "REVERSAL_ADD_PNL_MIN", -0.70) or -0.70),
        "max_hold_sec": int(getattr(TRADING_RULES, "REVERSAL_ADD_MAX_HOLD_SEC", 180) or 180),
        "min_ai_score": int(getattr(TRADING_RULES, "REVERSAL_ADD_MIN_AI_SCORE", 60) or 60),
        "min_ai_recovery_delta": int(getattr(TRADING_RULES, "REVERSAL_ADD_MIN_AI_RECOVERY_DELTA", 15) or 15),
    }
    blocked = [event for event in events if str(event.get("stage") or "") == "reversal_add_blocked_reason"]
    candidates = [event for event in events if str(event.get("stage") or "") == "reversal_add_candidate"]
    reason_counter = Counter(str((event.get("fields") or {}).get("reason") or "") for event in blocked)
    pnl_values = [_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in blocked + candidates]
    hold_values = [_safe_float((event.get("fields") or {}).get("held_sec"), None) for event in blocked + candidates]
    ai_values = [_safe_float((event.get("fields") or {}).get("ai_score"), None) for event in blocked + candidates]
    recovery_values = [_safe_float((event.get("fields") or {}).get("ai_recovery_delta"), None) for event in blocked + candidates]
    pnl_values = [v for v in pnl_values if v is not None]
    hold_values = [v for v in hold_values if v is not None]
    ai_values = [v for v in ai_values if v is not None]
    recovery_values = [v for v in recovery_values if v is not None]
    sample_ready = len(candidates) >= 20
    recommended = {
        "pnl_min": round(_clamp(_percentile(pnl_values, 20, current["pnl_min"]), -1.3, -0.3), 2),
        "max_hold_sec": int(round(_clamp(_percentile(hold_values, 80, current["max_hold_sec"]), 120.0, 900.0))),
        "min_ai_score": int(round(_clamp(_percentile(ai_values, 30, current["min_ai_score"]), 45.0, 75.0))),
        "min_ai_recovery_delta": int(round(_clamp(_percentile(recovery_values, 30, current["min_ai_recovery_delta"]), 5.0, 30.0))),
    }
    return {
        "family": "reversal_add",
        "stage": "holding_exit",
        "sample": {"blocked": len(blocked), "candidate": len(candidates)},
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "first-fail 로그면 all-predicate 복원이 안 되므로 상한 추정치로만 본다.",
            f"주요 blocker={dict(reason_counter.most_common(3))}",
        ],
    }


def _build_soft_stop_family(events: list[dict]) -> dict:
    current = {
        "grace_sec": int(getattr(TRADING_RULES, "SCALP_SOFT_STOP_MICRO_GRACE_SEC", 20) or 20),
        "emergency_pct": float(getattr(TRADING_RULES, "SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT", -2.0) or -2.0),
    }
    touches = [event for event in events if str(event.get("stage") or "") == "soft_stop_micro_grace"]
    profit_values = [_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in touches]
    hold_values = [_safe_float((event.get("fields") or {}).get("held_sec"), None) for event in touches]
    profit_values = [v for v in profit_values if v is not None]
    hold_values = [v for v in hold_values if v is not None]
    sample_ready = len(touches) >= 30
    recommended = {
        "grace_sec": int(round(_clamp(_percentile(hold_values, 25, current["grace_sec"]), 10.0, 60.0))),
        "emergency_pct": round(_clamp(_percentile(profit_values, 10, current["emergency_pct"]), -2.5, -1.5), 2),
    }
    return {
        "family": "soft_stop_micro_grace",
        "stage": "holding_exit",
        "sample": {"touches": len(touches)},
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "rebound/missed-upside 연결이 없으면 grace_sec 추천은 direction-only로 본다.",
            "holding_exit stage는 same-day 다른 live owner와 동시 적용 금지다.",
        ],
    }


def _build_family_reports(events: list[dict]) -> list[dict]:
    return [
        _build_mechanical_entry_family(events),
        _build_pre_submit_guard_family(events),
        _build_bad_entry_family(events),
        _build_reversal_add_family(events),
        _build_soft_stop_family(events),
    ]


def _build_apply_candidate_list(families: list[dict]) -> list[dict]:
    candidates: list[dict] = []
    entry_candidates = [family for family in families if family["stage"] == "entry" and family["apply_ready"]]
    holding_candidates = [family for family in families if family["stage"] == "holding_exit" and family["apply_ready"]]
    for group in (entry_candidates[:1], holding_candidates[:1]):
        for family in group:
            candidates.append(
                {
                    "family": family["family"],
                    "stage": family["stage"],
                    "apply_mode": family["apply_mode"],
                    "owner_rule": "single_axis_canary",
                }
            )
    return candidates


def _build_rollback_guard_pack(families: list[dict]) -> list[dict]:
    guards: list[dict] = []
    for family in families:
        if not family["apply_ready"]:
            continue
        guards.append(
            {
                "family": family["family"],
                "loss_cap": "COMPLETED + valid profit_rate avg <= -0.30% or realized pnl regression",
                "quality_regression": "submitted/full/partial 또는 soft/hard/trailing quality regression",
                "cross_contamination": "same-stage multi-owner contamination 금지",
                "sample_floor": "sample 부족 시 자동 승격 금지",
            }
        )
    return guards


def build_daily_threshold_cycle_report(
    target_date: str,
    *,
    pipeline_loader: Callable[[str], list[dict]] | None = None,
    completed_rows_loader: Callable[[str, str], list[dict]] | None = None,
    skip_completed_rows: bool = False,
) -> dict:
    target_date = str(target_date).strip()
    ctx = ThresholdCycleContext(warnings=[])
    custom_pipeline_loader = pipeline_loader
    completed_rows_loader = completed_rows_loader or _default_completed_rows_loader

    same_day = _date_range(target_date, 1)
    rolling_3d = _date_range(target_date, 3)
    rolling_7d = _date_range(target_date, 7)

    event_windows: dict[str, list[dict]] = {}
    pipeline_meta_by_date: dict[str, dict] = {}
    for label, dates in {"same_day": same_day, "rolling_3d": rolling_3d, "rolling_7d": rolling_7d}.items():
        rows: list[dict] = []
        for event_date in dates:
            try:
                if custom_pipeline_loader is None:
                    load_result = _default_pipeline_load_result(event_date)
                    rows.extend(load_result.rows)
                    pipeline_meta_by_date[event_date] = load_result.meta
                    for warning in load_result.meta.get("warnings", []):
                        ctx.warnings.append(f"pipeline event 로드 경고({event_date}): {warning}")
                else:
                    rows.extend(custom_pipeline_loader(event_date))
            except Exception as exc:
                ctx.warnings.append(f"pipeline event 로드 실패({event_date}): {exc}")
        event_windows[label] = rows

    completed_rows: list[dict] = []
    if not skip_completed_rows:
        try:
            completed_rows = completed_rows_loader(rolling_7d[0], rolling_7d[-1])
        except Exception as exc:
            ctx.warnings.append(f"completed trade 로드 실패: {exc}")
    else:
        ctx.warnings.append("completed trade 로드는 skip-db 옵션으로 생략됨")

    families = _build_family_reports(event_windows["same_day"])
    completed = _completed_summary(completed_rows)
    threshold_snapshot = {
        family["family"]: {
            "stage": family["stage"],
            "sample": family["sample"],
            "apply_ready": family["apply_ready"],
            "current": family["current"],
            "recommended": family["recommended"],
        }
        for family in families
    }
    threshold_diff_report = [
        {
            "family": family["family"],
            "stage": family["stage"],
            "apply_ready": family["apply_ready"],
            "current": family["current"],
            "recommended": family["recommended"],
            "notes": family["notes"],
        }
        for family in families
    ]
    report = {
        "date": target_date,
        "meta": {
            "schema_version": THRESHOLD_CYCLE_SCHEMA_VERSION,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_path": str(report_path_for_date(target_date)),
            "pipeline_load": pipeline_meta_by_date,
        },
        "windows": {
            "same_day": same_day,
            "rolling_3d": rolling_3d,
            "rolling_7d": rolling_7d,
        },
        "summary": {
            "completed_valid_rolling_7d": completed["completed_valid"],
            "loss_count_rolling_7d": completed["loss_count"],
            "event_count_same_day": len(event_windows["same_day"]),
        },
        "threshold_snapshot": threshold_snapshot,
        "threshold_diff_report": threshold_diff_report,
        "apply_candidate_list": _build_apply_candidate_list(families),
        "rollback_guard_pack": _build_rollback_guard_pack(families),
        "warnings": ctx.warnings,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build daily threshold cycle report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat(), help="Target date (YYYY-MM-DD)")
    parser.add_argument("--print", dest="print_stdout", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--skip-db", dest="skip_db", action="store_true", help="Skip completed trade DB lookup")
    args = parser.parse_args(argv)

    report = build_daily_threshold_cycle_report(args.target_date, skip_completed_rows=args.skip_db)
    save_threshold_cycle_report(report)
    if args.print_stdout:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
