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
from src.utils.threshold_cycle_registry import TARGET_STAGES, is_threshold_cycle_stage


REPORT_DIR = DATA_DIR / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
STAT_ACTION_REPORT_DIR = REPORT_DIR / "statistical_action_weight"
AI_DECISION_MATRIX_DIR = REPORT_DIR / "holding_exit_decision_matrix"
CUMULATIVE_THRESHOLD_REPORT_DIR = REPORT_DIR / "threshold_cycle_cumulative"
THRESHOLD_CYCLE_SCHEMA_VERSION = 1
THRESHOLD_CYCLE_DIR = DATA_DIR / "threshold_cycle"
RAW_PIPELINE_FALLBACK_MAX_BYTES = 64 * 1024 * 1024
CUMULATIVE_BASELINE_START_DATE = "2026-04-21"


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


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if value in (None, "", "-", "None"):
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%H:%M:%S"):
        try:
            parsed = datetime.strptime(text[:19] if "%Y" in fmt else text[:8], fmt)
            return parsed
        except Exception:
            continue
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _avg(values: list[float]) -> float | None:
    cleaned = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not cleaned:
        return None
    return sum(cleaned) / len(cleaned)


def _stddev(values: list[float]) -> float | None:
    cleaned = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if len(cleaned) < 2:
        return None
    mean = sum(cleaned) / len(cleaned)
    variance = sum((value - mean) ** 2 for value in cleaned) / (len(cleaned) - 1)
    return math.sqrt(max(variance, 0.0))


def _price_bucket(value: Any) -> str:
    price = _safe_float(value, None)
    if price is None or price <= 0:
        return "price_unknown"
    if price < 10_000:
        return "price_lt_10k"
    if price < 30_000:
        return "price_10k_30k"
    if price < 70_000:
        return "price_30k_70k"
    return "price_gte_70k"


def _volume_bucket(value: Any) -> str:
    volume = _safe_float(value, None)
    if volume is None or volume <= 0:
        return "volume_unknown"
    if volume < 500_000:
        return "volume_lt_500k"
    if volume < 2_000_000:
        return "volume_500k_2m"
    if volume < 10_000_000:
        return "volume_2m_10m"
    return "volume_gte_10m"


def _time_bucket(value: Any) -> str:
    dt_value = _parse_datetime(value)
    if dt_value is None:
        return "time_unknown"
    minute = dt_value.hour * 60 + dt_value.minute
    if minute < 9 * 60 or minute >= 15 * 60 + 30:
        return "time_outside_regular"
    if minute < 9 * 60 + 30:
        return "time_0900_0930"
    if minute < 10 * 60 + 30:
        return "time_0930_1030"
    if minute < 14 * 60:
        return "time_1030_1400"
    return "time_1400_1530"


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


def _date_range_between(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if start > end:
        return []
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


def statistical_action_report_paths(target_date: str) -> tuple[Path, Path]:
    return (
        STAT_ACTION_REPORT_DIR / f"statistical_action_weight_{target_date}.json",
        STAT_ACTION_REPORT_DIR / f"statistical_action_weight_{target_date}.md",
    )


def holding_exit_decision_matrix_paths(target_date: str) -> tuple[Path, Path]:
    return (
        AI_DECISION_MATRIX_DIR / f"holding_exit_decision_matrix_{target_date}.json",
        AI_DECISION_MATRIX_DIR / f"holding_exit_decision_matrix_{target_date}.md",
    )


def cumulative_threshold_report_paths(target_date: str) -> tuple[Path, Path]:
    return (
        CUMULATIVE_THRESHOLD_REPORT_DIR / f"threshold_cycle_cumulative_{target_date}.json",
        CUMULATIVE_THRESHOLD_REPORT_DIR / f"threshold_cycle_cumulative_{target_date}.md",
    )


def _import_sqlalchemy():
    from sqlalchemy import create_engine, text

    return create_engine, text


def _default_completed_rows_loader(start_date: str, end_date: str) -> list[dict]:
    create_engine, text = _import_sqlalchemy()
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    query = text(
        """
        SELECT
            rh.rec_date,
            rh.stock_code,
            rh.stock_name,
            rh.status,
            rh.strategy,
            rh.buy_price,
            rh.buy_qty,
            rh.buy_time,
            rh.sell_price,
            rh.sell_time,
            rh.profit_rate,
            rh.add_count,
            rh.avg_down_count,
            rh.pyramid_count,
            rh.last_add_type,
            dsq.volume AS daily_volume,
            dsq.marcap AS marcap
        FROM recommendation_history rh
        LEFT JOIN LATERAL (
            SELECT volume, marcap
            FROM daily_stock_quotes dsq
            WHERE dsq.stock_code = rh.stock_code
              AND dsq.quote_date <= rh.rec_date
            ORDER BY dsq.quote_date DESC
            LIMIT 1
        ) dsq ON true
        WHERE rh.rec_date >= :start_date
          AND rh.rec_date <= :end_date
          AND rh.status = 'COMPLETED'
          AND rh.profit_rate IS NOT NULL
        ORDER BY rh.rec_date DESC, rh.stock_code
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
            if not is_threshold_cycle_stage(
                str(payload.get("stage") or ""),
                payload.get("fields") if isinstance(payload.get("fields"), dict) else None,
            ):
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
                if not is_threshold_cycle_stage(
                    str(payload.get("stage") or ""),
                    payload.get("fields") if isinstance(payload.get("fields"), dict) else None,
                ):
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


def _row_rec_date(row: dict) -> date | None:
    value = row.get("rec_date") or row.get("date") or row.get("trade_date")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value in (None, "", "-", "None"):
        return None
    text = str(value).strip()[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except Exception:
        return None


def _filter_completed_rows_by_date(rows: list[dict], start_date: str, end_date: str) -> list[dict]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    filtered: list[dict] = []
    missing_date_rows: list[dict] = []
    for row in rows:
        rec_date = _row_rec_date(row)
        if rec_date is None:
            missing_date_rows.append(row)
            continue
        if start <= rec_date <= end:
            filtered.append(row)
    if not filtered and missing_date_rows and start <= end:
        return list(missing_date_rows)
    return filtered


def _valid_profit_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if _safe_float(row.get("profit_rate"), None) is not None]


def _is_normal_only_row(row: dict) -> bool:
    markers = [
        row.get("strategy"),
        row.get("entry_type"),
        row.get("order_type"),
        row.get("cohort"),
        row.get("source"),
    ]
    joined = " ".join(str(value or "").lower() for value in markers)
    return "fallback" not in joined and "remote" not in joined and "songstock" not in joined


def _is_initial_only_row(row: dict) -> bool:
    add_count = _safe_int(row.get("add_count"), 0) or 0
    avg_down_count = _safe_int(row.get("avg_down_count"), 0) or 0
    pyramid_count = _safe_int(row.get("pyramid_count"), 0) or 0
    last_add_type = str(row.get("last_add_type") or "").strip().upper()
    return add_count <= 0 and avg_down_count <= 0 and pyramid_count <= 0 and not last_add_type


def _completed_profit_summary(rows: list[dict]) -> dict:
    valid_rows = _valid_profit_rows(rows)
    profit_values = [_safe_float(row.get("profit_rate"), None) for row in valid_rows]
    profit_values = [value for value in profit_values if value is not None]
    wins = [value for value in profit_values if value > 0]
    losses = [value for value in profit_values if value < 0]
    return {
        "sample": len(profit_values),
        "win_count": len(wins),
        "loss_count": len(losses),
        "avg_profit_rate": round(_avg(profit_values) or 0.0, 4) if profit_values else None,
        "median_profit_rate": round(_percentile(profit_values, 50, 0.0), 4) if profit_values else None,
        "downside_p10_profit_rate": round(_percentile(profit_values, 10, 0.0), 4) if profit_values else None,
        "upside_p90_profit_rate": round(_percentile(profit_values, 90, 0.0), 4) if profit_values else None,
        "win_rate": round(len(wins) / len(profit_values), 4) if profit_values else None,
        "loss_rate": round(len(losses) / len(profit_values), 4) if profit_values else None,
        "stddev_profit_rate": round(_stddev(profit_values) or 0.0, 4) if len(profit_values) >= 2 else None,
    }


def _completed_cohort_summary(rows: list[dict]) -> dict:
    valid_rows = _valid_profit_rows(rows)
    cohorts = {
        "all_completed_valid": valid_rows,
        "normal_only": [row for row in valid_rows if _is_normal_only_row(row)],
        "initial_only": [row for row in valid_rows if _is_initial_only_row(row)],
        "pyramid_activated": [
            row
            for row in valid_rows
            if (_safe_int(row.get("pyramid_count"), 0) or 0) > 0
            or str(row.get("last_add_type") or "").strip().upper() == "PYRAMID"
        ],
        "reversal_add_activated": [
            row
            for row in valid_rows
            if (_safe_int(row.get("avg_down_count"), 0) or 0) > 0
            or str(row.get("last_add_type") or "").strip().upper() in {"AVG_DOWN", "REVERSAL_ADD"}
        ],
    }
    return {name: _completed_profit_summary(cohort_rows) for name, cohort_rows in cohorts.items()}


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
    refined_candidates = [
        event for event in events if str(event.get("stage") or "") == "bad_entry_refined_candidate"
    ]
    refined_exits = [event for event in events if str(event.get("stage") or "") == "bad_entry_refined_exit"]
    exclusion_counter = Counter(
        str((event.get("fields") or {}).get("exclusion_reason") or "-") for event in refined_candidates
    )
    soft_stop_zone_candidates = [
        event
        for event in refined_candidates
        if str((event.get("fields") or {}).get("exclusion_reason") or "") == "soft_stop_zone"
    ]
    early_capture_candidates = [
        event
        for event in refined_candidates
        if str((event.get("fields") or {}).get("exclusion_reason") or "") not in ("soft_stop_zone", "-")
        and str((event.get("fields") or {}).get("should_exit") or "").lower() == "true"
    ]
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
        "sample": {
            "observed": len(observed),
            "refined_candidate": len(refined_candidates),
            "refined_exit": len(refined_exits),
            "soft_stop_zone_candidate": len(soft_stop_zone_candidates),
            "early_capture_candidate": len(early_capture_candidates),
            "exclusion_top": dict(exclusion_counter.most_common(5)),
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "today live block은 열지 않고 observe->postclose->next_preopen 순서만 허용한다.",
            "후행 soft_stop/hard_stop 연결이 불충분하면 추천값은 shadow 유지다.",
            "soft_stop_zone_candidate는 refined canary가 이미 soft stop 영역에 들어간 뒤 제외한 표본이다.",
            "early_capture_candidate가 0이면 soft stop threshold보다 앞서 잡을 수 있었던 표본은 아직 확인되지 않은 것으로 본다.",
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
    reason_counter = Counter(
        str((event.get("fields") or {}).get("blocked_reason") or (event.get("fields") or {}).get("reason") or "-")
        for event in blocked
    )
    predicate_names = (
        "pnl_ok",
        "hold_ok",
        "low_floor_ok",
        "ai_score_ok",
        "ai_recover_ok",
        "supply_ok",
        "buy_pressure_ok",
        "tick_accel_ok",
        "large_sell_absent_ok",
        "micro_vwap_ok",
    )
    predicate_pass_counts = {
        name: sum(1 for event in blocked if str((event.get("fields") or {}).get(name) or "").lower() == "true")
        for name in predicate_names
    }
    all_but_hold = sum(
        1
        for event in blocked
        if str((event.get("fields") or {}).get("hold_ok") or "").lower() != "true"
        and all(
            str((event.get("fields") or {}).get(name) or "").lower() == "true"
            for name in predicate_names
            if name != "hold_ok"
        )
    )
    all_but_ai_recovery = sum(
        1
        for event in blocked
        if str((event.get("fields") or {}).get("ai_recover_ok") or "").lower() != "true"
        and all(
            str((event.get("fields") or {}).get(name) or "").lower() == "true"
            for name in predicate_names
            if name != "ai_recover_ok"
        )
    )
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
        "sample": {
            "blocked": len(blocked),
            "candidate": len(candidates),
            "blocker_top": dict(reason_counter.most_common(5)),
            "predicate_pass_counts": predicate_pass_counts,
            "near_miss_all_but_hold": all_but_hold,
            "near_miss_all_but_ai_recovery": all_but_ai_recovery,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "first-fail 로그면 all-predicate 복원이 안 되므로 상한 추정치로만 본다.",
            f"주요 blocker={dict(reason_counter.most_common(3))}",
            "near_miss_all_but_*는 한 축만 열면 체결됐을 가능성이 있는 표본 수다. 0이면 복합조건 미충족으로 본다.",
        ],
    }


def _build_scalp_trailing_take_profit_family(events: list[dict]) -> dict:
    current = {
        "start_pct": float(getattr(TRADING_RULES, "SCALP_TRAILING_START_PCT", 0.6) or 0.6),
        "weak_limit": float(getattr(TRADING_RULES, "SCALP_TRAILING_LIMIT_WEAK", 0.4) or 0.4),
        "strong_limit": float(getattr(TRADING_RULES, "SCALP_TRAILING_LIMIT_STRONG", 0.8) or 0.8),
        "strong_ai_score": 75,
    }
    trailing_exits = [
        event
        for event in events
        if str(event.get("stage") or "") == "exit_signal"
        and str((event.get("fields") or {}).get("exit_rule") or "") == "scalp_trailing_take_profit"
    ]
    completed = [
        event
        for event in events
        if str(event.get("stage") or "") == "sell_completed"
        and str((event.get("fields") or {}).get("exit_rule") or "") == "scalp_trailing_take_profit"
    ]
    pyramid_signaled_ids = {
        event.get("record_id")
        for event in events
        if str(event.get("stage") or "") == "stat_action_decision_snapshot"
        and (
            str((event.get("fields") or {}).get("chosen_action") or "") == "pyramid_wait"
            or str((event.get("fields") or {}).get("scale_in_action_type") or "") == "PYRAMID"
        )
        and event.get("record_id") is not None
    }
    pyramid_executed_ids = {
        event.get("record_id")
        for event in events
        if str(event.get("stage") or "") in {"scale_in_executed", "scale_in_completed"}
        and event.get("record_id") is not None
    }
    drawdown_values: list[float] = []
    profit_values: list[float] = []
    ai_values: list[float] = []
    weak_borderline = 0
    would_hold_if_weak_plus_10bp = 0
    would_hold_if_strong_ai_relaxed_5pt = 0
    initial_only = 0
    pyramid_signaled_not_executed = 0
    pyramid_executed = 0
    borderline_examples: list[dict] = []
    strong_ai_boundary_examples: list[dict] = []
    for event in trailing_exits:
        fields = event.get("fields") or {}
        profit = _safe_float(fields.get("profit_rate"), None)
        peak = _safe_float(fields.get("peak_profit"), None)
        ai_score = _safe_float(fields.get("current_ai_score"), None)
        record_id = event.get("record_id")
        if record_id in pyramid_executed_ids:
            pyramid_executed += 1
            pyramid_state = "pyramid_executed"
        elif record_id in pyramid_signaled_ids:
            pyramid_signaled_not_executed += 1
            pyramid_state = "pyramid_signaled_not_executed"
        else:
            initial_only += 1
            pyramid_state = "initial_only"
        if profit is not None:
            profit_values.append(profit)
        if ai_score is not None:
            ai_values.append(ai_score)
        if profit is None or peak is None:
            continue
        drawdown = peak - profit
        drawdown_values.append(drawdown)
        limit = current["strong_limit"] if (ai_score or 0) >= current["strong_ai_score"] else current["weak_limit"]
        limit_bucket = "strong" if (ai_score or 0) >= current["strong_ai_score"] else "weak"
        if abs(drawdown - limit) <= 0.05:
            weak_borderline += 1
        if (ai_score or 0) < current["strong_ai_score"] and drawdown < current["weak_limit"] + 0.10:
            would_hold_if_weak_plus_10bp += 1
        strong_ai_boundary = (
            ai_score is not None
            and current["strong_ai_score"] - 5 <= ai_score < current["strong_ai_score"]
            and drawdown < current["strong_limit"]
        )
        if strong_ai_boundary:
            would_hold_if_strong_ai_relaxed_5pt += 1
        if abs(drawdown - limit) <= 0.10 and len(borderline_examples) < 8:
            borderline_examples.append(
                {
                    "emitted_at": event.get("emitted_at"),
                    "stock_code": event.get("stock_code"),
                    "stock_name": event.get("stock_name"),
                    "record_id": record_id,
                    "profit_rate": round(profit, 4),
                    "peak_profit": round(peak, 4),
                    "drawdown_from_peak": round(drawdown, 4),
                    "current_ai_score": round(ai_score, 2) if ai_score is not None else None,
                    "active_limit": round(limit, 4),
                    "limit_bucket": limit_bucket,
                    "pyramid_state": pyramid_state,
                    "would_hold_if_weak_limit_plus_10bp": bool(
                        (ai_score or 0) < current["strong_ai_score"]
                        and drawdown < current["weak_limit"] + 0.10
                    ),
                }
            )
        if strong_ai_boundary and len(strong_ai_boundary_examples) < 8:
            strong_ai_boundary_examples.append(
                {
                    "emitted_at": event.get("emitted_at"),
                    "stock_code": event.get("stock_code"),
                    "stock_name": event.get("stock_name"),
                    "record_id": record_id,
                    "profit_rate": round(profit, 4),
                    "peak_profit": round(peak, 4),
                    "drawdown_from_peak": round(drawdown, 4),
                    "current_ai_score": round(ai_score, 2),
                    "active_limit": round(limit, 4),
                    "strong_limit": round(current["strong_limit"], 4),
                    "pyramid_state": pyramid_state,
                }
            )
    completed_profit_values = [
        value
        for value in (_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in completed)
        if value is not None
    ]
    sample_ready = len(trailing_exits) >= 20
    recommended_weak = _clamp(_percentile(drawdown_values, 60, current["weak_limit"]), 0.4, 0.8)
    return {
        "family": "scalp_trailing_take_profit",
        "stage": "holding_exit",
        "sample": {
            "exit_signal": len(trailing_exits),
            "completed": len(completed),
            "avg_profit_rate_at_signal": round(_avg(profit_values) or 0.0, 4) if profit_values else None,
            "avg_completed_profit_rate": round(_avg(completed_profit_values) or 0.0, 4)
            if completed_profit_values
            else None,
            "avg_drawdown_from_peak": round(_avg(drawdown_values) or 0.0, 4) if drawdown_values else None,
            "weak_borderline": weak_borderline,
            "would_hold_if_weak_limit_plus_10bp": would_hold_if_weak_plus_10bp,
            "would_hold_if_strong_ai_score_relaxed_5pt": would_hold_if_strong_ai_relaxed_5pt,
            "initial_only": initial_only,
            "pyramid_signaled_not_executed": pyramid_signaled_not_executed,
            "pyramid_executed": pyramid_executed,
            "borderline_examples": borderline_examples,
            "strong_ai_boundary_examples": strong_ai_boundary_examples,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": {
            "weak_limit": round(recommended_weak, 2),
            "strong_limit": current["strong_limit"],
        },
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "일반 트레일링 익절 민감도 표본이다. protect_trailing_smoothing과 합산하지 않는다.",
            "pyramid_signaled_not_executed는 불타기 조건은 열렸지만 실제 추가 체결 없이 일반 보유 수량으로 청산된 표본이다.",
            "weak_borderline은 현행 weak limit 근처에서 잘린 표본이며, missed-upside와 연결되기 전에는 live 변경 근거가 아니다.",
            "would_hold_if_weak_limit_plus_10bp는 +0.10%p 완화 시 같은 tick에서 청산되지 않았을 후보 수다.",
            "would_hold_if_strong_ai_score_relaxed_5pt는 AI strong 경계 5점 이내에서 strong limit를 적용했다면 같은 tick 청산이 보류됐을 후보 수다.",
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


def _build_protect_trailing_smoothing_family(events: list[dict]) -> dict:
    current = {
        "window_sec": int(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC", 20) or 20),
        "min_span_sec": int(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC", 8) or 8),
        "min_samples": int(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES", 3) or 3),
        "below_ratio": float(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO", 0.67) or 0.67),
        "buffer_pct": float(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT", 1.0) or 1.0),
        "emergency_pct": float(getattr(TRADING_RULES, "SCALP_PROTECT_TRAILING_EMERGENCY_PCT", -2.0) or -2.0),
    }
    holds = [event for event in events if str(event.get("stage") or "") == "protect_trailing_smooth_hold"]
    confirmed = [event for event in events if str(event.get("stage") or "") == "protect_trailing_smooth_confirmed"]
    completed = [
        event
        for event in events
        if str(event.get("stage") or "") == "sell_completed"
        and str((event.get("fields") or {}).get("exit_rule") or "") == "protect_trailing_stop"
    ]
    candidate_events = holds + confirmed
    span_values = [_safe_float((event.get("fields") or {}).get("sample_span_sec"), None) for event in candidate_events]
    sample_values = [_safe_float((event.get("fields") or {}).get("sample_count"), None) for event in candidate_events]
    below_values = [_safe_float((event.get("fields") or {}).get("below_ratio"), None) for event in candidate_events]
    buffer_values = [_safe_float((event.get("fields") or {}).get("buffer_pct"), None) for event in candidate_events]
    emergency_values = [_safe_float((event.get("fields") or {}).get("emergency_pct"), None) for event in candidate_events]
    profit_values = [_safe_float((event.get("fields") or {}).get("profit_rate"), None) for event in completed]
    span_values = [v for v in span_values if v is not None]
    sample_values = [v for v in sample_values if v is not None]
    below_values = [v for v in below_values if v is not None]
    buffer_values = [v for v in buffer_values if v is not None]
    emergency_values = [v for v in emergency_values if v is not None]
    profit_values = [v for v in profit_values if v is not None]
    sample_ready = len(candidate_events) >= 20 and (len(confirmed) + len(holds)) >= 20
    recommended = {
        "window_sec": int(round(_clamp(_percentile(span_values, 90, current["window_sec"]), 10.0, 45.0))),
        "min_span_sec": int(round(_clamp(_percentile(span_values, 50, current["min_span_sec"]), 5.0, 20.0))),
        "min_samples": int(round(_clamp(_percentile(sample_values, 50, current["min_samples"]), 3.0, 8.0))),
        "below_ratio": round(_clamp(_percentile(below_values, 75, current["below_ratio"]), 0.50, 0.90), 2),
        "buffer_pct": round(_clamp(_percentile(buffer_values, 50, current["buffer_pct"]), 0.50, 1.50), 2),
        "emergency_pct": round(_clamp(_percentile(emergency_values, 10, current["emergency_pct"]), -2.5, -1.5), 2),
    }
    return {
        "family": "protect_trailing_smoothing",
        "stage": "holding_exit",
        "sample": {
            "smooth_hold": len(holds),
            "smooth_confirmed": len(confirmed),
            "protect_trailing_completed": len(completed),
            "completed_avg_profit_rate": round(_avg(profit_values) or 0.0, 4) if profit_values else None,
        },
        "apply_ready": sample_ready,
        "current": current,
        "recommended": recommended,
        "apply_mode": "next_preopen_single_owner" if sample_ready else "observe_only",
        "notes": [
            "protect_trailing smoothing 값은 장중 자동 변경하지 않고 장후 report와 다음 장전 manifest 후보로만 산출한다.",
            "protect_hard_stop과 emergency_pct 이탈은 평탄화 대상이 아니므로 별도 safety로 유지한다.",
            "sample floor 미달이면 추천값은 direction-only이며 리노공업 단일 케이스로 live 재조정하지 않는다.",
        ],
    }


def _action_label_for_completed_row(row: dict) -> str:
    last_add_type = str(row.get("last_add_type") or "").strip().upper()
    avg_down_count = _safe_int(row.get("avg_down_count"), 0) or 0
    pyramid_count = _safe_int(row.get("pyramid_count"), 0) or 0
    if avg_down_count > 0 or last_add_type == "AVG_DOWN":
        return "avg_down_wait"
    if pyramid_count > 0 or last_add_type == "PYRAMID":
        return "pyramid_wait"
    return "exit_only"


def _summarize_action_rows(rows: list[dict]) -> dict:
    profit_values = [_safe_float(row.get("profit_rate"), None) for row in rows]
    profit_values = [value for value in profit_values if value is not None]
    if not profit_values:
        return {
            "sample": len(rows),
            "avg_profit_rate": None,
            "median_profit_rate": None,
            "downside_p10_profit_rate": None,
            "stddev_profit_rate": None,
            "win_rate": None,
            "loss_rate": None,
        }
    wins = [value for value in profit_values if value > 0]
    losses = [value for value in profit_values if value < 0]
    return {
        "sample": len(profit_values),
        "avg_profit_rate": round(_avg(profit_values) or 0.0, 4),
        "median_profit_rate": round(_percentile(profit_values, 50, 0.0), 4),
        "downside_p10_profit_rate": round(_percentile(profit_values, 10, 0.0), 4),
        "stddev_profit_rate": round(_stddev(profit_values) or 0.0, 4),
        "win_rate": round(len(wins) / len(profit_values), 4),
        "loss_rate": round(len(losses) / len(profit_values), 4),
    }


def _confidence_adjusted_action_score(summary: dict, prior_summary: dict, *, prior_strength: int = 8) -> dict:
    sample = int(summary.get("sample") or 0)
    avg_profit = _safe_float(summary.get("avg_profit_rate"), None)
    prior_avg = _safe_float(prior_summary.get("avg_profit_rate"), 0.0) or 0.0
    if sample <= 0 or avg_profit is None:
        return {
            "empirical_bayes_profit_rate": None,
            "uncertainty_penalty": None,
            "confidence_adjusted_score": None,
            "weight": 0.0,
        }
    smoothed = ((avg_profit * sample) + (prior_avg * prior_strength)) / (sample + prior_strength)
    stddev = _safe_float(summary.get("stddev_profit_rate"), None)
    if stddev is None or stddev <= 0:
        stddev = abs(avg_profit - prior_avg) or 0.5
    uncertainty_penalty = stddev / math.sqrt(sample)
    score = smoothed - uncertainty_penalty
    weight = _clamp((score + 1.0) / 2.0, 0.0, 1.0)
    return {
        "empirical_bayes_profit_rate": round(smoothed, 4),
        "uncertainty_penalty": round(uncertainty_penalty, 4),
        "confidence_adjusted_score": round(score, 4),
        "weight": round(weight, 4),
    }


def _best_action_by_bucket(rows: list[dict], bucket_field: str, *, min_sample: int = 5) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((str(row.get(bucket_field) or "unknown"), str(row.get("action_label") or "exit_only")), []).append(row)

    global_rows_by_action = {
        action: [row for row in rows if str(row.get("action_label") or "exit_only") == action]
        for action in ("exit_only", "avg_down_wait", "pyramid_wait")
    }
    global_summary_by_action = {
        action: _summarize_action_rows(action_rows)
        for action, action_rows in global_rows_by_action.items()
    }
    buckets = sorted({bucket for bucket, _ in grouped})
    recommendations: list[dict] = []
    for bucket in buckets:
        action_summaries = []
        for action in ("exit_only", "avg_down_wait", "pyramid_wait"):
            summary = _summarize_action_rows(grouped.get((bucket, action), []))
            score_pack = _confidence_adjusted_action_score(summary, global_summary_by_action[action])
            action_summaries.append({"action": action, **summary, **score_pack})
        eligible = [
            item for item in action_summaries
            if item["sample"] >= min_sample and item["confidence_adjusted_score"] is not None
        ]
        ranked = sorted(eligible, key=lambda item: item["confidence_adjusted_score"], reverse=True)
        best = ranked[0] if ranked else None
        runner_up = ranked[1] if len(ranked) > 1 else None
        margin = (
            round(best["confidence_adjusted_score"] - runner_up["confidence_adjusted_score"], 4)
            if best and runner_up
            else None
        )
        if not best:
            policy_hint = "insufficient_sample"
        elif best["loss_rate"] is not None and best["loss_rate"] >= 0.65:
            policy_hint = "defensive_only_high_loss_rate"
        elif margin is not None and margin < 0.15:
            policy_hint = "no_clear_edge"
        else:
            policy_hint = "candidate_weight_source"
        recommendations.append(
            {
                "bucket": bucket,
                "best_action": best["action"] if best else "insufficient_sample",
                "best_avg_profit_rate": best["avg_profit_rate"] if best else None,
                "best_confidence_adjusted_score": best["confidence_adjusted_score"] if best else None,
                "edge_margin": margin,
                "policy_hint": policy_hint,
                "actions": action_summaries,
            }
        )
    return recommendations


def _build_statistical_action_weight_family(events: list[dict], completed_rows: list[dict]) -> dict:
    completed_valid: list[dict] = []
    for row in completed_rows:
        profit_rate = _safe_float(row.get("profit_rate"), None)
        if profit_rate is None:
            continue
        enriched = dict(row)
        enriched["action_label"] = _action_label_for_completed_row(row)
        enriched["price_bucket"] = _price_bucket(row.get("buy_price"))
        enriched["volume_bucket"] = _volume_bucket(
            row.get("daily_volume")
            or row.get("volume")
            or row.get("acc_volume")
            or row.get("trade_volume")
        )
        enriched["time_bucket"] = _time_bucket(row.get("buy_time") or row.get("sell_time"))
        completed_valid.append(enriched)

    action_counts = Counter(row["action_label"] for row in completed_valid)
    action_summary = {
        action: _summarize_action_rows([row for row in completed_valid if row["action_label"] == action])
        for action in ("exit_only", "avg_down_wait", "pyramid_wait")
    }
    known_price = sum(1 for row in completed_valid if row["price_bucket"] != "price_unknown")
    known_volume = sum(1 for row in completed_valid if row["volume_bucket"] != "volume_unknown")
    known_time = sum(1 for row in completed_valid if row["time_bucket"] != "time_unknown")
    event_counts = Counter(str(event.get("stage") or "") for event in events)
    sample_ready = (
        len(completed_valid) >= 50
        and known_price >= 30
        and known_time >= 30
        and (action_counts.get("avg_down_wait", 0) + action_counts.get("pyramid_wait", 0)) >= 10
    )
    return {
        "family": "statistical_action_weight",
        "stage": "decision_support",
        "sample": {
            "completed_valid": len(completed_valid),
            "exit_only": action_counts.get("exit_only", 0),
            "avg_down_wait": action_counts.get("avg_down_wait", 0),
            "pyramid_wait": action_counts.get("pyramid_wait", 0),
            "compact_exit_signal": event_counts.get("exit_signal", 0),
            "compact_sell_completed": event_counts.get("sell_completed", 0),
            "compact_scale_in_executed": event_counts.get("scale_in_executed", 0),
            "compact_decision_snapshot": event_counts.get("stat_action_decision_snapshot", 0),
        },
        "apply_ready": False,
        "weight_source_ready": sample_ready,
        "current": {
            "mode": "report_only",
            "live_runtime_mutation": False,
            "bucket_axes": ["price_bucket", "volume_bucket", "time_bucket"],
            "score_method": "empirical_bayes_lower_confidence_bound",
        },
        "recommended": {
            "action_summary": action_summary,
            "by_price_bucket": _best_action_by_bucket(completed_valid, "price_bucket"),
            "by_volume_bucket": _best_action_by_bucket(completed_valid, "volume_bucket"),
            "by_time_bucket": _best_action_by_bucket(completed_valid, "time_bucket"),
            "data_completeness": {
                "price_known": known_price,
                "volume_known": known_volume,
                "time_known": known_time,
            },
            "weight_governor": {
                "min_bucket_action_sample": 5,
                "prior_strength": 8,
                "clear_edge_margin": 0.15,
                "high_loss_rate_guard": 0.65,
            },
        },
        "apply_mode": "report_only_weight_source",
        "notes": [
            "가격대/거래량/시간대별 exit_only vs avg_down_wait vs pyramid_wait 통계 축이다.",
            "작은 표본은 action별 전체 prior로 shrinkage하고 불확실성 penalty를 뺀 confidence-adjusted score로만 비교한다.",
            "live 청산/추가매수 판단에는 직접 적용하지 않고 장후 threshold weight 입력으로만 사용한다.",
            "거래량 표본이 부족하면 volume_bucket 결론은 금지하고 price/time bucket만 direction-only로 본다.",
        ],
    }


def _build_family_reports(events: list[dict], completed_rows: list[dict] | None = None) -> list[dict]:
    completed_rows = completed_rows or []
    return [
        _build_mechanical_entry_family(events),
        _build_pre_submit_guard_family(events),
        _build_bad_entry_family(events),
        _build_reversal_add_family(events),
        _build_soft_stop_family(events),
        _build_scalp_trailing_take_profit_family(events),
        _build_protect_trailing_smoothing_family(events),
        _build_statistical_action_weight_family(events, completed_rows),
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


def _markdown_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _best_action_row(bucket: dict) -> dict:
    best_action = bucket.get("best_action")
    actions = bucket.get("actions") if isinstance(bucket.get("actions"), list) else []
    for action in actions:
        if action.get("action") == best_action:
            return action
    return {}


def _render_bucket_markdown(title: str, rows: list[dict]) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        lines.extend(["- 표본 없음", ""])
        return lines
    lines.append("| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in rows:
        best = _best_action_row(row)
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(row.get("bucket")),
                    _markdown_value(row.get("best_action")),
                    _markdown_value(row.get("best_confidence_adjusted_score")),
                    _markdown_value(row.get("edge_margin")),
                    _markdown_value(best.get("sample")),
                    _markdown_value(best.get("avg_profit_rate")),
                    _markdown_value(best.get("loss_rate")),
                    _markdown_value(row.get("policy_hint")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def build_statistical_action_weight_artifact(report: dict) -> dict:
    target_date = str(report.get("date") or date.today().isoformat())
    family = (report.get("threshold_snapshot") or {}).get("statistical_action_weight") or {}
    recommended = family.get("recommended") if isinstance(family.get("recommended"), dict) else {}
    sample = family.get("sample") if isinstance(family.get("sample"), dict) else {}
    rows = []
    for axis, key in (
        ("price_bucket", "by_price_bucket"),
        ("volume_bucket", "by_volume_bucket"),
        ("time_bucket", "by_time_bucket"),
    ):
        for row in recommended.get(key) or []:
            if not isinstance(row, dict):
                continue
            rows.append({"axis": axis, **row})
    policy_counts = Counter(str(row.get("policy_hint") or "-") for row in rows)
    artifact = {
        "date": target_date,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_report": str(report_path_for_date(target_date)),
        "family": "statistical_action_weight",
        "sample": sample,
        "weight_source_ready": bool(family.get("weight_source_ready")),
        "current": family.get("current") or {},
        "recommended": recommended,
        "policy_counts": dict(policy_counts),
        "operator_decision": (
            "candidate_weight_source_review"
            if policy_counts.get("candidate_weight_source", 0) > 0
            else "collect_more_samples"
        ),
        "runtime_change": False,
        "runtime_change_reason": "statistical_action_weight is report-only until a separate owner/canary is approved",
    }
    return artifact


def render_statistical_action_weight_markdown(artifact: dict) -> str:
    sample = artifact.get("sample") if isinstance(artifact.get("sample"), dict) else {}
    recommended = artifact.get("recommended") if isinstance(artifact.get("recommended"), dict) else {}
    data_completeness = recommended.get("data_completeness") if isinstance(recommended.get("data_completeness"), dict) else {}
    policy_counts = artifact.get("policy_counts") if isinstance(artifact.get("policy_counts"), dict) else {}
    lines = [
        f"# Statistical Action Weight Report - {artifact.get('date')}",
        "",
        "## 판정",
        "",
        f"- 상태: `{artifact.get('operator_decision')}`",
        f"- weight_source_ready: `{bool(artifact.get('weight_source_ready'))}`",
        "- runtime_change: `False`",
        "",
        "## 표본 충분성",
        "",
        "| metric | value |",
        "| --- | ---: |",
    ]
    for key in (
        "completed_valid",
        "exit_only",
        "avg_down_wait",
        "pyramid_wait",
        "compact_exit_signal",
        "compact_sell_completed",
        "compact_scale_in_executed",
        "compact_decision_snapshot",
    ):
        lines.append(f"| {key} | {_markdown_value(sample.get(key))} |")
    lines.extend(["", "## 데이터 완성도", "", "| field | known |", "| --- | ---: |"])
    for key in ("price_known", "volume_known", "time_known"):
        lines.append(f"| {key} | {_markdown_value(data_completeness.get(key))} |")
    lines.extend(["", "## Policy Counts", "", "| policy | count |", "| --- | ---: |"])
    for key, value in sorted(policy_counts.items()):
        lines.append(f"| {key} | {_markdown_value(value)} |")
    lines.append("")
    lines.extend(_render_bucket_markdown("Price Bucket", recommended.get("by_price_bucket") or []))
    lines.extend(_render_bucket_markdown("Volume Bucket", recommended.get("by_volume_bucket") or []))
    lines.extend(_render_bucket_markdown("Time Bucket", recommended.get("by_time_bucket") or []))
    lines.extend(
        [
            "## Threshold 반영 원칙",
            "",
            "- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.",
            "- `candidate_weight_source`는 다음 threshold weight 또는 decision matrix 후보일 뿐이다.",
            "- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 live 반영 금지다.",
            "",
            "## 다음 액션",
            "",
            "- Markdown 자동생성 상태와 표본 충분성을 확인한다.",
            "- sample-ready이면 `holding_exit_decision_matrix`와 shadow prompt 주입 후보로 넘긴다.",
            "- 부족하면 `stat_action_decision_snapshot`와 completed/action join 품질을 먼저 보강한다.",
            "",
        ]
    )
    return "\n".join(lines)


def save_statistical_action_weight_artifact(report: dict) -> tuple[Path, Path]:
    artifact = build_statistical_action_weight_artifact(report)
    json_path, md_path = statistical_action_report_paths(str(artifact.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_statistical_action_weight_markdown(artifact), encoding="utf-8")
    return json_path, md_path


def _recommended_bias_for_bucket(row: dict) -> str:
    if row.get("policy_hint") != "candidate_weight_source":
        return "no_clear_edge"
    if row.get("edge_margin") is None:
        return "no_clear_edge"
    if "unknown" in str(row.get("bucket") or ""):
        return "no_clear_edge"
    best_action = str(row.get("best_action") or "")
    if best_action == "exit_only":
        return "prefer_exit"
    if best_action == "avg_down_wait":
        return "prefer_avg_down_wait"
    if best_action == "pyramid_wait":
        return "prefer_pyramid_wait"
    return "no_clear_edge"


def _prompt_hint_for_matrix_entry(axis: str, row: dict, bias: str) -> str:
    bucket = row.get("bucket")
    if bias == "prefer_exit":
        return f"{axis}={bucket} 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다."
    if bias == "prefer_avg_down_wait":
        return f"{axis}={bucket} 과거 표본은 회복형 물타기 대기 후보가 상대적으로 우위다. 저점 미갱신과 수급 회복이 없으면 무시한다."
    if bias == "prefer_pyramid_wait":
        return f"{axis}={bucket} 과거 표본은 winner size-up 대기 후보가 상대적으로 우위다. trailing giveback과 체결품질을 확인한다."
    return f"{axis}={bucket} 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다."


def build_holding_exit_decision_matrix(report: dict) -> dict:
    target_date = str(report.get("date") or date.today().isoformat())
    family = (report.get("threshold_snapshot") or {}).get("statistical_action_weight") or {}
    recommended = family.get("recommended") if isinstance(family.get("recommended"), dict) else {}
    entries: list[dict] = []
    for axis, key in (
        ("price_bucket", "by_price_bucket"),
        ("volume_bucket", "by_volume_bucket"),
        ("time_bucket", "by_time_bucket"),
    ):
        for row in recommended.get(key) or []:
            if not isinstance(row, dict):
                continue
            best = _best_action_row(row)
            bias = _recommended_bias_for_bucket(row)
            entries.append(
                {
                    "axis": axis,
                    "bucket": row.get("bucket"),
                    "recommended_bias": bias,
                    "confidence_adjusted_score": row.get("best_confidence_adjusted_score"),
                    "edge_margin": row.get("edge_margin"),
                    "sample": best.get("sample"),
                    "loss_rate": best.get("loss_rate"),
                    "downside_p10_profit_rate": best.get("downside_p10_profit_rate"),
                    "policy_hint": row.get("policy_hint"),
                    "prompt_hint": _prompt_hint_for_matrix_entry(axis, row, bias),
                }
            )
    return {
        "matrix_version": f"holding_exit_decision_matrix_v1_{target_date}",
        "source_report": str(report_path_for_date(target_date)),
        "source_date": target_date,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "valid_for_date": "next_preopen",
        "runtime_change": False,
        "application_mode": "shadow_prompt_or_observe_only_until_owner_approval",
        "hard_veto": [
            "emergency_or_hard_stop",
            "active_sell_order_pending",
            "invalid_feature",
            "post_add_eval_exclusion",
        ],
        "entries": entries,
        "notes": [
            "장중 self-updating 금지: 장후 산정 matrix를 다음 장전 로드하고 장중에는 immutable context로만 사용한다.",
            "AI 점수를 직접 덮어쓰지 않는다. shadow prompt 또는 observe-only nudge부터 검증한다.",
        ],
    }


def render_holding_exit_decision_matrix_markdown(matrix: dict) -> str:
    lines = [
        f"# Holding/Exit Decision Matrix - {matrix.get('source_date')}",
        "",
        "## 판정",
        "",
        f"- matrix_version: `{matrix.get('matrix_version')}`",
        f"- application_mode: `{matrix.get('application_mode')}`",
        "- runtime_change: `False`",
        "",
        "## Hard Veto",
        "",
    ]
    for item in matrix.get("hard_veto") or []:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Matrix Entries",
            "",
            "| axis | bucket | bias | score | edge | sample | loss_rate | policy |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for entry in matrix.get("entries") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(entry.get("axis")),
                    _markdown_value(entry.get("bucket")),
                    _markdown_value(entry.get("recommended_bias")),
                    _markdown_value(entry.get("confidence_adjusted_score")),
                    _markdown_value(entry.get("edge_margin")),
                    _markdown_value(entry.get("sample")),
                    _markdown_value(entry.get("loss_rate")),
                    _markdown_value(entry.get("policy_hint")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Prompt Hints", ""])
    for entry in matrix.get("entries") or []:
        lines.append(
            f"- `{entry.get('axis')}={entry.get('bucket')}` / `{entry.get('recommended_bias')}`: "
            f"{entry.get('prompt_hint')}"
        )
    lines.extend(
        [
            "",
            "## 다음 액션",
            "",
            "- `ADM-2`에서는 이 matrix를 holding/exit shadow prompt context로만 주입한다.",
            "- action_label/confidence/reason drift를 보고 observe-only nudge 여부를 판정한다.",
            "- single-owner canary 승인 전에는 live AI 응답을 바꾸지 않는다.",
            "",
        ]
    )
    return "\n".join(lines)


def save_holding_exit_decision_matrix(report: dict) -> tuple[Path, Path]:
    matrix = build_holding_exit_decision_matrix(report)
    json_path, md_path = holding_exit_decision_matrix_paths(str(matrix.get("source_date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_holding_exit_decision_matrix_markdown(matrix), encoding="utf-8")
    return json_path, md_path


def _threshold_snapshot_from_families(families: list[dict], *, report_only: bool = False) -> dict:
    snapshot: dict[str, dict] = {}
    for family in families:
        payload = {
            "stage": family["stage"],
            "sample": family["sample"],
            "apply_ready": False if report_only else family["apply_ready"],
            "sample_ready": family["apply_ready"],
            "weight_source_ready": family.get("weight_source_ready", family["apply_ready"]),
            "apply_mode": "report_only_reference" if report_only else family.get("apply_mode"),
            "current": family["current"],
            "recommended": family["recommended"],
        }
        if report_only:
            payload["daily_family_apply_mode"] = family.get("apply_mode")
        snapshot[family["family"]] = payload
    return snapshot


def build_cumulative_threshold_cycle_report(
    target_date: str,
    *,
    start_date: str = CUMULATIVE_BASELINE_START_DATE,
    rolling_days: tuple[int, ...] = (5, 10, 20),
    pipeline_loader: Callable[[str], list[dict]] | None = None,
    completed_rows_loader: Callable[[str, str], list[dict]] | None = None,
    skip_completed_rows: bool = False,
) -> dict:
    target_date = str(target_date).strip()
    start_date = str(start_date).strip()
    ctx = ThresholdCycleContext(warnings=[])
    custom_pipeline_loader = pipeline_loader
    completed_rows_loader = completed_rows_loader or _default_completed_rows_loader

    window_dates: dict[str, list[str]] = {"cumulative": _date_range_between(start_date, target_date)}
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    for days in rolling_days:
        window_dates[f"rolling_{days}d"] = [
            value for value in _date_range(target_date, days)
            if datetime.strptime(value, "%Y-%m-%d").date() >= start_dt
        ]

    events_by_window: dict[str, list[dict]] = {}
    pipeline_meta_by_date: dict[str, dict] = {}
    for label, dates in window_dates.items():
        rows: list[dict] = []
        for event_date in dates:
            try:
                if custom_pipeline_loader is None:
                    load_result = _default_pipeline_load_result(event_date)
                    rows.extend(load_result.rows)
                    pipeline_meta_by_date.setdefault(event_date, load_result.meta)
                    for warning in load_result.meta.get("warnings", []):
                        ctx.warnings.append(f"pipeline event 로드 경고({label}/{event_date}): {warning}")
                else:
                    rows.extend(custom_pipeline_loader(event_date))
            except Exception as exc:
                ctx.warnings.append(f"pipeline event 로드 실패({label}/{event_date}): {exc}")
        events_by_window[label] = rows

    completed_rows: list[dict] = []
    if not skip_completed_rows:
        try:
            completed_rows = completed_rows_loader(start_date, target_date)
        except Exception as exc:
            ctx.warnings.append(f"completed trade 로드 실패: {exc}")
    else:
        ctx.warnings.append("completed trade 로드는 skip-db 옵션으로 생략됨")

    completed_by_window: dict[str, list[dict]] = {}
    for label, dates in window_dates.items():
        if not dates:
            completed_by_window[label] = []
            continue
        completed_by_window[label] = _filter_completed_rows_by_date(completed_rows, dates[0], dates[-1])

    family_snapshots: dict[str, dict] = {}
    family_apply_candidates: dict[str, list[dict]] = {}
    for label in window_dates:
        families = _build_family_reports(events_by_window.get(label, []), completed_by_window.get(label, []))
        family_snapshots[label] = _threshold_snapshot_from_families(families, report_only=True)
        family_apply_candidates[label] = []

    completed_summary_by_window = {
        label: _completed_cohort_summary(rows)
        for label, rows in completed_by_window.items()
    }
    event_count_by_window = {label: len(rows) for label, rows in events_by_window.items()}
    source_flags = {
        "profit_basis": "COMPLETED + valid profit_rate only",
        "runtime_change": False,
        "application_mode": "report_only_cumulative_threshold_input",
        "live_threshold_mutation": False,
        "main_only_field_available": False,
        "full_partial_fill_split_available": False,
        "full_partial_fill_split_note": "completed trade loader does not expose fill-completion ratio; do not use cumulative PnL to merge full/partial fill cohorts",
    }
    return {
        "date": target_date,
        "start_date": start_date,
        "meta": {
            "schema_version": THRESHOLD_CYCLE_SCHEMA_VERSION,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_path": str(cumulative_threshold_report_paths(target_date)[0]),
            "pipeline_load": pipeline_meta_by_date,
        },
        "windows": window_dates,
        "summary": {
            "event_count_by_window": event_count_by_window,
            "completed_valid_cumulative": completed_summary_by_window["cumulative"]["all_completed_valid"]["sample"],
            "rolling_windows": list(window_dates.keys()),
        },
        "completed_cohorts": completed_summary_by_window,
        "threshold_snapshot_by_window": family_snapshots,
        "apply_candidate_list_by_window": family_apply_candidates,
        "source_flags": source_flags,
        "operator_decision": "report_only_review",
        "next_action_policy": [
            "daily와 cumulative/rolling이 같은 방향을 가리킬 때만 threshold 후보로 올린다.",
            "누적 평균 단독으로 live threshold mutation 또는 bot restart를 수행하지 않는다.",
            "full/partial fill split, fallback/source cohort, runtime flag cohort가 누락되면 손익 결론을 방향성으로 격하한다.",
        ],
        "warnings": ctx.warnings,
    }


def render_cumulative_threshold_cycle_markdown(report: dict) -> str:
    lines = [
        f"# Cumulative Threshold Cycle Report - {report.get('date')}",
        "",
        "## 판정",
        "",
        f"- 상태: `{report.get('operator_decision')}`",
        "- runtime_change: `False`",
        f"- 기준 구간: `{report.get('start_date')}` ~ `{report.get('date')}`",
        "- 손익 기준: `COMPLETED + valid profit_rate only`",
        "",
        "## Window Summary",
        "",
        "| window | dates | events | completed | avg_profit | win_rate | loss_rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    windows = report.get("windows") if isinstance(report.get("windows"), dict) else {}
    event_counts = (report.get("summary") or {}).get("event_count_by_window") or {}
    completed = report.get("completed_cohorts") if isinstance(report.get("completed_cohorts"), dict) else {}
    for label, dates in windows.items():
        all_completed = (completed.get(label) or {}).get("all_completed_valid") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_value(label),
                    _markdown_value(len(dates) if isinstance(dates, list) else None),
                    _markdown_value(event_counts.get(label)),
                    _markdown_value(all_completed.get("sample")),
                    _markdown_value(all_completed.get("avg_profit_rate")),
                    _markdown_value(all_completed.get("win_rate")),
                    _markdown_value(all_completed.get("loss_rate")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Cohort Summary",
            "",
            "| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for label, cohort_pack in completed.items():
        if not isinstance(cohort_pack, dict):
            continue
        for cohort, summary in cohort_pack.items():
            if not isinstance(summary, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_value(label),
                        _markdown_value(cohort),
                        _markdown_value(summary.get("sample")),
                        _markdown_value(summary.get("avg_profit_rate")),
                        _markdown_value(summary.get("downside_p10_profit_rate")),
                        _markdown_value(summary.get("upside_p90_profit_rate")),
                        _markdown_value(summary.get("win_rate")),
                        _markdown_value(summary.get("loss_rate")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Family Readiness",
            "",
            "| window | family | stage | sample | sample_ready | apply_mode |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    snapshots = report.get("threshold_snapshot_by_window") if isinstance(report.get("threshold_snapshot_by_window"), dict) else {}
    for label, snapshot in snapshots.items():
        if not isinstance(snapshot, dict):
            continue
        for family, payload in snapshot.items():
            sample = payload.get("sample") if isinstance(payload.get("sample"), dict) else {}
            sample_value = sample.get("completed_valid") or sample.get("observed") or sample.get("exit_signal") or sample.get("budget_pass")
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_value(label),
                        _markdown_value(family),
                        _markdown_value(payload.get("stage")),
                        _markdown_value(sample_value),
                        _markdown_value(payload.get("sample_ready")),
                        _markdown_value(payload.get("apply_mode")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## 사용 금지선",
            "",
            "- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.",
            "- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.",
            "- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.",
            "",
            "## 다음 액션",
            "",
            "- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.",
            "- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.",
            "- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.",
            "",
        ]
    )
    return "\n".join(lines)


def save_cumulative_threshold_cycle_report(report: dict) -> tuple[Path, Path]:
    json_path, md_path = cumulative_threshold_report_paths(str(report.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_cumulative_threshold_cycle_markdown(report), encoding="utf-8")
    return json_path, md_path


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

    families = _build_family_reports(event_windows["same_day"], completed_rows)
    completed = _completed_summary(completed_rows)
    threshold_snapshot = {
        family["family"]: {
            "stage": family["stage"],
            "sample": family["sample"],
            "apply_ready": family["apply_ready"],
            "weight_source_ready": family.get("weight_source_ready", family["apply_ready"]),
            "apply_mode": family.get("apply_mode"),
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
    save_statistical_action_weight_artifact(report)
    save_holding_exit_decision_matrix(report)
    cumulative_report = build_cumulative_threshold_cycle_report(args.target_date, skip_completed_rows=args.skip_db)
    save_cumulative_threshold_cycle_report(cumulative_report)
    if args.print_stdout:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
