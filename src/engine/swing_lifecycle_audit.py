"""Swing full-lifecycle audit and self-improvement automation reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from sqlalchemy import create_engine, text

from src.engine.ai_response_contracts import build_openai_response_text_format
from src.engine.swing_selection_funnel_report import (
    SWING_EVENT_STAGES,
    SWING_STRATEGIES,
    load_recommendation_rows,
    summarize_pipeline_events,
    summarize_recommendation_rows,
)
from src.model.common_v2 import RECO_DIAGNOSTIC_JSON_PATH, RECO_PATH, SWING_SELECTION_OWNER
from src.utils.constants import DATA_DIR, POSTGRES_URL


REPORT_TYPE = "swing_lifecycle_audit"
SCHEMA_VERSION = 1
AUTOMATION_SCHEMA_VERSION = 1
THRESHOLD_REVIEW_SCHEMA_VERSION = 1

SWING_LIFECYCLE_OWNER = "SwingFullLifecycleSelfImprovementChain"
SWING_LIFECYCLE_AUDIT_DIR = Path(DATA_DIR) / "report" / "swing_lifecycle_audit"
SWING_THRESHOLD_AI_REVIEW_DIR = Path(DATA_DIR) / "report" / "swing_threshold_ai_review"
SWING_IMPROVEMENT_AUTOMATION_DIR = Path(DATA_DIR) / "report" / "swing_improvement_automation"

ENTRY_STAGES = {
    "blocked_swing_gap",
    "gatekeeper_fast_reuse",
    "gatekeeper_fast_reuse_bypass",
    "blocked_gatekeeper_reject",
    "blocked_gatekeeper_missing",
    "blocked_gatekeeper_error",
    "market_regime_block",
    "market_regime_pass",
    "order_bundle_submitted",
    "order_submitted",
    "buy_order_submitted",
    "swing_sim_buy_order_assumed_filled",
    "swing_sim_order_bundle_assumed_filled",
}
HOLDING_STAGE_TOKENS = ("holding", "hold_", "mfe", "mae")
SCALE_IN_STAGE_TOKENS = ("scale_in", "pyramid", "avg_down", "reversal_add")
EXIT_STAGE_TOKENS = ("sell", "exit", "trim", "time_stop", "trailing")
SIMULATED_STAGES = {
    "swing_sim_buy_order_assumed_filled",
    "swing_sim_order_bundle_assumed_filled",
    "swing_sim_scale_in_order_assumed_filled",
    "swing_sim_sell_order_assumed_filled",
}
SUBMITTED_STAGES = {"order_bundle_submitted", "order_submitted", "buy_order_submitted"}
SELL_STAGES = {
    "swing_sim_sell_order_assumed_filled",
    "sell_order_sent",
    "sell_order_submitted",
    "sell_order_failed",
    "sell_order_blocked_market_closed",
}
AI_CONTRACT_ISSUES = [
    {
        "issue_id": "swing_gatekeeper_free_text_label",
        "severity": "medium",
        "lifecycle_stage": "entry",
        "current_contract": "free_text_report_label",
        "target_contract": "structured_outputs_candidate",
        "reason": "Gatekeeper entry is currently reconstructed from report labels instead of a strict swing entry schema.",
    },
    {
        "issue_id": "swing_holding_flow_scalping_prompt_reuse",
        "severity": "medium",
        "lifecycle_stage": "holding_exit",
        "current_contract": "scalping_holding_flow_prompt_reused",
        "target_contract": "swing_holding_exit_schema_candidate",
        "reason": "Swing sell candidates can pass through holding-flow review that is named and tuned for scalping.",
    },
    {
        "issue_id": "swing_scale_in_ai_contract_missing",
        "severity": "low",
        "lifecycle_stage": "scale_in",
        "current_contract": "deterministic_pyramid_only",
        "target_contract": "swing_scale_in_schema_candidate",
        "reason": "Swing PYRAMID/AVG_DOWN observation is not yet represented by a dedicated AI proposal contract.",
    },
]

SWING_THRESHOLD_FAMILIES = [
    {
        "family": "swing_model_floor",
        "lifecycle_stage": "selection",
        "current_surface": "recommend_daily_v2 floor_bull/floor_bear",
        "bounds": {"min": 0.20, "max": 0.70},
        "max_step_per_day": 0.05,
        "sample_floor": 3,
        "sample_window": "rolling_5d",
        "rollback_guard": "selected_count_zero_or_fallback_contamination",
        "source_metrics": ["selected_count", "safe_pool_count", "fallback_written_to_recommendations"],
    },
    {
        "family": "swing_selection_top_k",
        "lifecycle_stage": "selection",
        "current_surface": "daily recommendation top-k",
        "bounds": {"min": 1, "max": 10},
        "max_step_per_day": 1,
        "sample_floor": 3,
        "sample_window": "rolling_5d",
        "rollback_guard": "db_load_gap_or_candidate_quality_deterioration",
        "source_metrics": ["csv_rows", "db_rows", "selection_modes"],
    },
    {
        "family": "swing_gatekeeper_accept_reject",
        "lifecycle_stage": "entry",
        "current_surface": "gatekeeper action label accept/reject",
        "bounds": None,
        "max_step_per_day": None,
        "sample_floor": 5,
        "sample_window": "rolling_5d",
        "rollback_guard": "submitted_quality_or_bad_entry_deterioration",
        "source_metrics": ["blocked_gatekeeper_reject", "gatekeeper_actions", "gatekeeper_eval_ms"],
    },
    {
        "family": "swing_gatekeeper_reject_cooldown",
        "lifecycle_stage": "entry",
        "current_surface": "gatekeeper reject cooldown seconds",
        "bounds": {"min": 300, "max": 7200},
        "max_step_per_day": 600,
        "sample_floor": 5,
        "sample_window": "rolling_5d",
        "rollback_guard": "repeat_reject_churn_or_missed_entry_degradation",
        "source_metrics": ["cooldown_sec", "cooldown_policy", "gatekeeper_actions"],
    },
    {
        "family": "swing_market_regime_sensitivity",
        "lifecycle_stage": "entry",
        "current_surface": "market regime hard block/pass",
        "bounds": None,
        "max_step_per_day": None,
        "sample_floor": 3,
        "sample_window": "rolling_10d",
        "rollback_guard": "bull_regime_blocked_good_entry_or_bear_regime_loss",
        "source_metrics": ["market_regime_block", "market_regime_pass", "bull_regime"],
    },
    {
        "family": "swing_pyramid_trigger",
        "lifecycle_stage": "scale_in",
        "current_surface": "SWING_PYRAMID_MIN_PROFIT_PCT and drawdown from peak",
        "bounds": {"min": 1.0, "max": 8.0},
        "max_step_per_day": 0.5,
        "sample_floor": 3,
        "sample_window": "rolling_10d",
        "rollback_guard": "post_add_mae_or_winner_dilution",
        "source_metrics": ["PYRAMID", "post_add_outcome", "peak_drawdown"],
    },
    {
        "family": "swing_avg_down_eligibility",
        "lifecycle_stage": "scale_in",
        "current_surface": "AVG_DOWN disabled/report-only candidate",
        "bounds": None,
        "max_step_per_day": None,
        "sample_floor": 5,
        "sample_window": "rolling_10d",
        "rollback_guard": "loss_extension_or_position_cap_pressure",
        "source_metrics": ["AVG_DOWN", "drawdown", "recovery_signal", "post_add_outcome"],
    },
    {
        "family": "swing_trailing_stop_time_stop",
        "lifecycle_stage": "exit",
        "current_surface": "strategy-specific trailing/stop/time-stop rules",
        "bounds": None,
        "max_step_per_day": None,
        "sample_floor": 5,
        "sample_window": "rolling_10d",
        "rollback_guard": "good_exit_removal_or_missed_upside",
        "source_metrics": ["exit_source", "time_stop", "trailing", "post_sell_rebound"],
    },
    {
        "family": "swing_holding_flow_defer",
        "lifecycle_stage": "holding_exit",
        "current_surface": "holding_flow_override defer cost",
        "bounds": {"min": 0, "max": 90},
        "max_step_per_day": 15,
        "sample_floor": 5,
        "sample_window": "rolling_10d",
        "rollback_guard": "defer_cost_or_safety_exit_delay",
        "source_metrics": ["flow_action", "defer_sec", "worsen_after_candidate"],
    },
]


def _date_text(target_date: str | date | datetime) -> str:
    return str(pd.to_datetime(target_date).date())


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _safe_read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields")
    return fields if isinstance(fields, dict) else {}


def _event_stage(event: dict[str, Any]) -> str:
    return str(event.get("stage") or event.get("event") or "").strip()


def _event_strategy(event: dict[str, Any]) -> str:
    fields = _event_fields(event)
    return str(event.get("strategy") or fields.get("strategy") or "").strip().upper()


def _event_identity(event: dict[str, Any]) -> tuple[str, str, str]:
    fields = _event_fields(event)
    record_id = str(event.get("record_id") or fields.get("record_id") or "")
    code = str(event.get("stock_code") or fields.get("stock_code") or fields.get("code") or "")
    name = str(event.get("stock_name") or fields.get("stock_name") or fields.get("name") or "")
    return record_id, code, name


def _is_swing_event(event: dict[str, Any]) -> bool:
    stage = _event_stage(event)
    strategy = _event_strategy(event)
    if strategy in SWING_STRATEGIES:
        return True
    if stage in SUBMITTED_STAGES:
        return False
    if stage in SWING_EVENT_STAGES or stage in SELL_STAGES:
        return True
    if stage.startswith("swing_"):
        return True
    lowered = stage.lower()
    return "gatekeeper" in lowered or "market_regime" in lowered


def _stage_group(stage: str) -> str:
    lowered = stage.lower()
    if stage in ENTRY_STAGES or "gatekeeper" in lowered or "market_regime" in lowered:
        return "entry"
    if any(token in lowered for token in SCALE_IN_STAGE_TOKENS):
        return "scale_in"
    if stage in SELL_STAGES or any(token in lowered for token in EXIT_STAGE_TOKENS):
        return "exit"
    if any(token in lowered for token in HOLDING_STAGE_TOKENS):
        return "holding"
    return "other"


def _first_present(fields: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = fields.get(key)
        if value not in (None, ""):
            return value
    return None


def load_pipeline_event_rows(target_date: str | date | datetime) -> list[dict[str, Any]]:
    date_key = _date_text(target_date)
    return _read_jsonl(Path(DATA_DIR) / "pipeline_events" / f"pipeline_events_{date_key}.jsonl")


def load_db_lifecycle_rows(target_date: str, db_url: str = POSTGRES_URL) -> list[dict[str, Any]]:
    engine = create_engine(db_url)
    query = text(
        """
        SELECT rec_date, stock_code, stock_name, strategy, trade_type, position_tag,
               status, prob, buy_price, buy_qty, buy_time, sell_price, sell_qty,
               sell_time, profit_rate, profit, updated_at
        FROM recommendation_history
        WHERE rec_date = :target_date
          AND strategy IN ('KOSPI_ML', 'KOSDAQ_ML', 'MAIN')
        ORDER BY position_tag, stock_code
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"target_date": target_date})
    return df.to_dict("records")


def summarize_db_lifecycle_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    df = pd.DataFrame(list(rows))
    if df.empty:
        return {
            "db_rows": 0,
            "status_counts": {},
            "position_status_counts": {},
            "entered_rows": 0,
            "completed_rows": 0,
            "valid_profit_rows": 0,
            "avg_profit_rate": None,
            "realized_profit_sum": 0.0,
        }

    status = df.get("status", pd.Series(dtype=str)).fillna("UNKNOWN").astype(str)
    position = df.get("position_tag", pd.Series(dtype=str)).fillna("UNKNOWN").astype(str)
    buy_qty = pd.to_numeric(df.get("buy_qty", 0), errors="coerce").fillna(0)
    buy_time_present = df.get("buy_time", pd.Series([None] * len(df))).notna()
    profit_rate = pd.to_numeric(df.get("profit_rate", None), errors="coerce")
    profit = pd.to_numeric(df.get("profit", 0), errors="coerce").fillna(0)
    completed = status.eq("COMPLETED")
    valid_profit = completed & profit_rate.notna()

    return {
        "db_rows": int(len(df)),
        "status_counts": {str(k): int(v) for k, v in status.value_counts().to_dict().items()},
        "position_status_counts": {
            f"{pos}:{stat}": int(count)
            for (pos, stat), count in Counter(zip(position, status)).items()
        },
        "entered_rows": int(((buy_qty > 0) | buy_time_present).sum()),
        "completed_rows": int(completed.sum()),
        "valid_profit_rows": int(valid_profit.sum()),
        "avg_profit_rate": float(profit_rate[valid_profit].mean()) if bool(valid_profit.any()) else None,
        "realized_profit_sum": float(profit[completed].sum()),
    }


def summarize_lifecycle_events(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    raw_by_stage = Counter()
    unique_by_stage: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    raw_by_group = Counter()
    unique_by_group: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    field_coverage = Counter()
    gatekeeper_actions = Counter()
    cooldown_policies = Counter()
    add_types = Counter()
    exit_sources = Counter()
    actual_order_flags = Counter()
    by_record_timeline: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for event in events:
        if not _is_swing_event(event):
            continue
        stage = _event_stage(event)
        if not stage:
            continue
        fields = _event_fields(event)
        identity = _event_identity(event)
        group = _stage_group(stage)
        raw_by_stage[stage] += 1
        unique_by_stage[stage].add(identity)
        raw_by_group[group] += 1
        unique_by_group[group].add(identity)
        by_record_timeline[identity].append(
            {
                "stage": stage,
                "emitted_at": event.get("emitted_at"),
                "group": group,
                "fields": {
                    key: fields.get(key)
                    for key in (
                        "strategy",
                        "action",
                        "cooldown_sec",
                        "cooldown_policy",
                        "actual_order_submitted",
                        "add_type",
                        "scale_in_type",
                        "exit_source",
                        "sell_reason",
                        "profit_rate",
                    )
                    if key in fields
                },
            }
        )

        action = _first_present(fields, ("action", "gatekeeper_action", "flow_action"))
        if "gatekeeper" in stage and action is not None:
            gatekeeper_actions[str(action)] += 1
        cooldown_policy = fields.get("cooldown_policy")
        if cooldown_policy not in (None, ""):
            cooldown_policies[str(cooldown_policy)] += 1
        add_type = _first_present(fields, ("add_type", "scale_in_type", "candidate_action"))
        if add_type not in (None, "") and group == "scale_in":
            add_types[str(add_type).upper()] += 1
        exit_source = _first_present(fields, ("exit_source", "sell_reason", "reason", "decision_source"))
        if exit_source not in (None, "") and group == "exit":
            exit_sources[str(exit_source)] += 1
        actual_order = fields.get("actual_order_submitted")
        if actual_order not in (None, ""):
            actual_order_flags[str(_safe_bool(actual_order)).lower()] += 1

        for key, value in fields.items():
            if value not in (None, ""):
                field_coverage[str(key)] += 1

    groups = sorted(set(raw_by_group) | {"entry", "holding", "scale_in", "exit", "other"})
    stages = sorted(set(raw_by_stage) | SWING_EVENT_STAGES | SELL_STAGES)
    return {
        "raw_counts": {stage: int(raw_by_stage.get(stage, 0)) for stage in stages},
        "unique_record_counts": {
            stage: int(len(unique_by_stage.get(stage, set()))) for stage in stages
        },
        "group_raw_counts": {group: int(raw_by_group.get(group, 0)) for group in groups},
        "group_unique_counts": {
            group: int(len(unique_by_group.get(group, set()))) for group in groups
        },
        "gatekeeper_actions": dict(gatekeeper_actions),
        "cooldown_policies": dict(cooldown_policies),
        "add_types": dict(add_types),
        "exit_sources": dict(exit_sources),
        "actual_order_submitted_flags": dict(actual_order_flags),
        "submitted_unique_records": int(
            len(set().union(*(unique_by_stage.get(stage, set()) for stage in SUBMITTED_STAGES)))
            if any(stage in unique_by_stage for stage in SUBMITTED_STAGES)
            else 0
        ),
        "simulated_order_unique_records": int(
            len(set().union(*(unique_by_stage.get(stage, set()) for stage in SIMULATED_STAGES)))
            if any(stage in unique_by_stage for stage in SIMULATED_STAGES)
            else 0
        ),
        "field_coverage": dict(field_coverage),
        "record_timeline_sample": [
            {
                "record_id": record_id,
                "code": code,
                "name": name,
                "events": sorted(events, key=lambda item: str(item.get("emitted_at") or ""))[:12],
            }
            for (record_id, code, name), events in list(by_record_timeline.items())[:10]
        ],
    }


def _coverage_count(events: dict[str, Any], keys: Iterable[str]) -> int:
    coverage = events.get("field_coverage") or {}
    return int(sum(_safe_int(coverage.get(key), 0) for key in keys))


def build_observation_axes(
    *,
    model_selection: dict[str, Any],
    recommendation_csv: dict[str, Any],
    db_summary: dict[str, Any],
    lifecycle_events: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_counts = lifecycle_events.get("raw_counts") or {}
    unique_counts = lifecycle_events.get("unique_record_counts") or {}

    axes = [
        {
            "axis_id": "swing_selection_model_floor",
            "lifecycle_stage": "selection",
            "threshold_family": "swing_model_floor",
            "sample_count": int(model_selection.get("selected_count") or recommendation_csv.get("csv_rows") or 0),
            "required_fields": ["selected_count", "floor_bull", "floor_bear", "safe_pool_count"],
            "observed_fields": [
                key
                for key in ("selected_count", "floor_bull", "floor_bear", "latest_stats")
                if model_selection.get(key) not in (None, {}, "")
            ],
        },
        {
            "axis_id": "swing_recommendation_db_load",
            "lifecycle_stage": "db_load",
            "threshold_family": "swing_selection_top_k",
            "sample_count": int(recommendation_csv.get("csv_rows") or db_summary.get("db_rows") or 0),
            "required_fields": ["csv_rows", "db_rows", "position_tag", "status"],
            "observed_fields": ["csv_rows", "db_rows"] if db_summary.get("db_rows") else ["csv_rows"],
        },
        {
            "axis_id": "swing_gatekeeper_accept_reject",
            "lifecycle_stage": "entry",
            "threshold_family": "swing_gatekeeper_accept_reject",
            "sample_count": int(
                unique_counts.get("blocked_gatekeeper_reject", 0)
                + unique_counts.get("market_regime_pass", 0)
                + unique_counts.get("swing_sim_buy_order_assumed_filled", 0)
                + unique_counts.get("swing_sim_order_bundle_assumed_filled", 0)
            ),
            "required_fields": ["action", "cooldown_sec", "gatekeeper_eval_ms", "gatekeeper_cache"],
            "observed_field_count": _coverage_count(
                lifecycle_events, ["action", "cooldown_sec", "gatekeeper_eval_ms", "gatekeeper_cache"]
            ),
        },
        {
            "axis_id": "swing_gap_market_budget_price_qty",
            "lifecycle_stage": "entry",
            "threshold_family": "swing_market_regime_sensitivity",
            "sample_count": int(
                unique_counts.get("blocked_swing_gap", 0)
                + unique_counts.get("market_regime_block", 0)
                + unique_counts.get("market_regime_pass", 0)
                + lifecycle_events.get("submitted_unique_records", 0)
                + lifecycle_events.get("simulated_order_unique_records", 0)
            ),
            "required_fields": ["gap_pct", "market_regime", "buy_qty", "order_price", "actual_order_submitted"],
            "observed_field_count": _coverage_count(
                lifecycle_events,
                ["gap_pct", "market_regime", "buy_qty", "order_price", "actual_order_submitted"],
            ),
        },
        {
            "axis_id": "swing_holding_mfe_mae_defer",
            "lifecycle_stage": "holding",
            "threshold_family": "swing_holding_flow_defer",
            "sample_count": int(lifecycle_events.get("group_unique_counts", {}).get("holding", 0)),
            "required_fields": ["mfe", "mae", "peak_profit", "defer_sec", "flow_action"],
            "observed_field_count": _coverage_count(
                lifecycle_events, ["mfe", "mae", "peak_profit", "defer_sec", "flow_action"]
            ),
        },
        {
            "axis_id": "swing_scale_in_avg_down_pyramid",
            "lifecycle_stage": "scale_in",
            "threshold_family": "swing_pyramid_trigger",
            "sample_count": int(lifecycle_events.get("group_unique_counts", {}).get("scale_in", 0)),
            "required_fields": ["add_type", "would_qty", "effective_qty", "price_policy", "post_add_outcome"],
            "observed_field_count": _coverage_count(
                lifecycle_events,
                ["add_type", "would_qty", "effective_qty", "price_policy", "post_add_outcome"],
            ),
        },
        {
            "axis_id": "swing_exit_post_sell_attribution",
            "lifecycle_stage": "exit",
            "threshold_family": "swing_trailing_stop_time_stop",
            "sample_count": int(
                lifecycle_events.get("group_unique_counts", {}).get("exit", 0)
                + db_summary.get("completed_rows", 0)
            ),
            "required_fields": ["exit_source", "sell_reason", "profit_rate", "post_sell_rebound"],
            "observed_field_count": _coverage_count(
                lifecycle_events, ["exit_source", "sell_reason", "profit_rate", "post_sell_rebound"]
            )
            + int(db_summary.get("valid_profit_rows", 0)),
        },
    ]
    for axis in axes:
        sample_count = int(axis.get("sample_count") or 0)
        observed = axis.get("observed_fields")
        observed_count = len(observed) if isinstance(observed, list) else int(axis.get("observed_field_count") or 0)
        if sample_count <= 0:
            status = "hold_sample"
        elif observed_count <= 0:
            status = "instrumentation_gap"
        else:
            status = "ready"
        axis["status"] = status
        axis["runtime_change"] = False
    return axes


def _model_selection_summary(diagnostic_summary: dict[str, Any]) -> dict[str, Any]:
    latest_stats = diagnostic_summary.get("latest_stats")
    if isinstance(latest_stats, list) and latest_stats:
        latest_stats_value = latest_stats[-1]
    else:
        latest_stats_value = latest_stats if isinstance(latest_stats, dict) else {}
    return {
        "owner": diagnostic_summary.get("owner", SWING_SELECTION_OWNER),
        "selection_mode": diagnostic_summary.get("selection_mode", "UNKNOWN"),
        "selected_count": int(diagnostic_summary.get("selected_count", 0) or 0),
        "floor_bull": diagnostic_summary.get("floor_bull"),
        "floor_bear": diagnostic_summary.get("floor_bear"),
        "safe_pool_count": diagnostic_summary.get("safe_pool_count")
        or (latest_stats_value or {}).get("safe_pool_count"),
        "fallback_written_to_recommendations": bool(
            diagnostic_summary.get("fallback_written_to_recommendations", False)
        ),
        "score_distribution": diagnostic_summary.get("score_distribution", {}),
        "latest_stats": latest_stats_value,
    }


def _source_paths(date_key: str, paths: dict[str, str | None] | None = None) -> dict[str, str | None]:
    base = {
        "recommendations_csv": str(RECO_PATH),
        "recommendation_diagnostic_json": str(RECO_DIAGNOSTIC_JSON_PATH),
        "pipeline_events": str(Path(DATA_DIR) / "pipeline_events" / f"pipeline_events_{date_key}.jsonl"),
    }
    if paths:
        base.update(paths)
    return base


def build_swing_lifecycle_audit_report(
    target_date: str | date | datetime,
    *,
    recommendation_rows: Iterable[dict[str, Any]] | pd.DataFrame | None = None,
    diagnostic_summary: dict[str, Any] | None = None,
    db_rows: Iterable[dict[str, Any]] | None = None,
    event_rows: Iterable[dict[str, Any]] | None = None,
    recommendation_path: str | Path = RECO_PATH,
    diagnostic_json_path: str | Path = RECO_DIAGNOSTIC_JSON_PATH,
    db_url: str = POSTGRES_URL,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    if recommendation_rows is None:
        recommendation_rows = load_recommendation_rows(recommendation_path)
    if isinstance(recommendation_rows, pd.DataFrame):
        recommendation_rows = recommendation_rows.to_dict("records")
    recommendation_rows = list(recommendation_rows or [])
    if diagnostic_summary is None:
        diagnostic_summary = _safe_read_json(diagnostic_json_path)
    if db_rows is None:
        try:
            db_rows = load_db_lifecycle_rows(date_key, db_url=db_url)
        except Exception as exc:
            db_rows = []
            diagnostic_summary = {**(diagnostic_summary or {}), "db_load_error": str(exc)}
    db_rows = list(db_rows or [])
    if event_rows is None:
        event_rows = load_pipeline_event_rows(date_key)
    event_rows = list(event_rows or [])

    model_selection = _model_selection_summary(diagnostic_summary or {})
    recommendation_csv = summarize_recommendation_rows(recommendation_rows)
    db_summary = summarize_db_lifecycle_rows(db_rows)
    pipeline_summary = summarize_pipeline_events(event_rows)
    lifecycle_events = summarize_lifecycle_events(event_rows)
    observation_axes = build_observation_axes(
        model_selection=model_selection,
        recommendation_csv=recommendation_csv,
        db_summary=db_summary,
        lifecycle_events=lifecycle_events,
    )
    status_counts = Counter(axis["status"] for axis in observation_axes)

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "owner": SWING_LIFECYCLE_OWNER,
        "runtime_change": False,
        "policy": {
            "scope": "selection_to_exit_full_lifecycle",
            "runtime_change": False,
            "live_guard_relaxation": False,
            "actual_order_submission_change": False,
            "workorder_authority": "manual_codex_request_only",
        },
        "source_paths": _source_paths(date_key),
        "model_selection": model_selection,
        "recommendation_csv": recommendation_csv,
        "db_lifecycle": db_summary,
        "pipeline_events": pipeline_summary,
        "lifecycle_events": lifecycle_events,
        "observation_axes": observation_axes,
        "observation_axis_summary": {
            "axis_count": len(observation_axes),
            "status_counts": dict(status_counts),
            "ready_count": int(status_counts.get("ready", 0)),
            "instrumentation_gap_count": int(status_counts.get("instrumentation_gap", 0)),
            "hold_sample_count": int(status_counts.get("hold_sample", 0)),
        },
        "threshold_families": SWING_THRESHOLD_FAMILIES,
        "ai_contract_audit": {
            "runtime_change": False,
            "contract_issues": AI_CONTRACT_ISSUES,
            "openai_target": {
                "api_surface": "Responses API",
                "output_contract": "Structured Outputs for future adopted workorders",
                "prompt_language_candidates": [
                    "current_korean_prompt",
                    "english_control_prompt_with_korean_raw_labels",
                    "strict_schema_only_prompt",
                ],
            },
        },
    }


def _family_metric_snapshot(audit_report: dict[str, Any], family: str) -> dict[str, Any]:
    events = audit_report.get("lifecycle_events") or {}
    raw = events.get("raw_counts") or {}
    unique = events.get("unique_record_counts") or {}
    model = audit_report.get("model_selection") or {}
    csv = audit_report.get("recommendation_csv") or {}
    db = audit_report.get("db_lifecycle") or {}
    if family == "swing_model_floor":
        return {
            "sample_count": int(model.get("selected_count") or 0),
            "selected_count": model.get("selected_count"),
            "safe_pool_count": model.get("safe_pool_count"),
            "fallback_written_to_recommendations": model.get("fallback_written_to_recommendations"),
        }
    if family == "swing_selection_top_k":
        return {
            "sample_count": int(csv.get("csv_rows") or 0),
            "csv_rows": csv.get("csv_rows"),
            "db_rows": db.get("db_rows"),
            "selection_modes": csv.get("selection_modes"),
        }
    if family == "swing_gatekeeper_accept_reject":
        return {
            "sample_count": int(unique.get("blocked_gatekeeper_reject", 0)),
            "blocked_gatekeeper_reject": raw.get("blocked_gatekeeper_reject", 0),
            "gatekeeper_actions": events.get("gatekeeper_actions"),
        }
    if family == "swing_gatekeeper_reject_cooldown":
        return {
            "sample_count": int(unique.get("blocked_gatekeeper_reject", 0)),
            "cooldown_policies": events.get("cooldown_policies"),
            "gatekeeper_actions": events.get("gatekeeper_actions"),
        }
    if family == "swing_market_regime_sensitivity":
        return {
            "sample_count": int(unique.get("market_regime_block", 0) + unique.get("market_regime_pass", 0)),
            "market_regime_block": raw.get("market_regime_block", 0),
            "market_regime_pass": raw.get("market_regime_pass", 0),
        }
    if family in {"swing_pyramid_trigger", "swing_avg_down_eligibility"}:
        return {
            "sample_count": int((events.get("group_unique_counts") or {}).get("scale_in", 0)),
            "add_types": events.get("add_types"),
        }
    if family == "swing_trailing_stop_time_stop":
        return {
            "sample_count": int((events.get("group_unique_counts") or {}).get("exit", 0) + db.get("completed_rows", 0)),
            "exit_sources": events.get("exit_sources"),
            "completed_rows": db.get("completed_rows"),
            "valid_profit_rows": db.get("valid_profit_rows"),
        }
    if family == "swing_holding_flow_defer":
        return {
            "sample_count": int((events.get("group_unique_counts") or {}).get("holding", 0)),
            "field_coverage": {
                key: (events.get("field_coverage") or {}).get(key, 0)
                for key in ("flow_action", "defer_sec", "worsen_after_candidate")
            },
        }
    return {"sample_count": 0}


def build_swing_threshold_candidates(audit_report: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for family_meta in SWING_THRESHOLD_FAMILIES:
        family = str(family_meta["family"])
        metrics = _family_metric_snapshot(audit_report, family)
        sample_count = int(metrics.get("sample_count") or 0)
        sample_floor = int(family_meta.get("sample_floor") or 0)
        if sample_count < sample_floor:
            state = "hold_sample"
        else:
            state = "hold"
        candidates.append(
            {
                "family": family,
                "lifecycle_stage": family_meta.get("lifecycle_stage"),
                "calibration_state": state,
                "recommended_value": None,
                "current_value": None,
                "sample_count": sample_count,
                "sample_floor": sample_floor,
                "sample_window": family_meta.get("sample_window"),
                "bounds": family_meta.get("bounds"),
                "max_step_per_day": family_meta.get("max_step_per_day"),
                "rollback_guard": family_meta.get("rollback_guard"),
                "source_metrics": metrics,
                "allowed_runtime_apply": False,
                "runtime_change": False,
            }
        )
    return candidates


ALLOWED_AI_STATES = {"agree", "correction_proposed", "caution", "insufficient_context", "safety_concern", "unavailable"}
ALLOWED_PROPOSED_STATES = {"adjust_up", "adjust_down", "hold", "hold_sample", "freeze", None}
ALLOWED_ANOMALY_ROUTES = {"threshold_candidate", "incident", "instrumentation_gap", "normal_drift", None}
ALLOWED_SAMPLE_WINDOWS = {"daily_intraday", "rolling_5d", "rolling_10d", "cumulative", None}


def _parse_ai_review_response(raw_response: Any | None) -> tuple[str, list[dict[str, Any]], list[str]]:
    if raw_response in (None, ""):
        return "unavailable", [], []
    if isinstance(raw_response, dict):
        payload = raw_response
    else:
        try:
            payload = json.loads(str(raw_response))
        except Exception as exc:
            return "parse_rejected", [], [f"json_parse_failed: {exc}"]
    if not isinstance(payload, dict):
        return "parse_rejected", [], ["top_level_not_object"]
    corrections = payload.get("corrections")
    if not isinstance(corrections, list):
        return "parse_rejected", [], ["corrections_not_array"]

    parsed: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, item in enumerate(corrections):
        if not isinstance(item, dict):
            warnings.append(f"corrections[{index}] not object")
            continue
        family = str(item.get("family") or "").strip()
        proposal = item.get("correction_proposal")
        if not family or not isinstance(proposal, dict):
            warnings.append(f"corrections[{index}] missing family/proposal")
            continue
        ai_state = item.get("ai_review_state")
        proposed_state = proposal.get("proposed_state")
        anomaly_route = proposal.get("anomaly_route")
        sample_window = proposal.get("sample_window")
        if ai_state not in ALLOWED_AI_STATES:
            warnings.append(f"corrections[{index}] invalid ai_review_state={ai_state}")
            continue
        if proposed_state not in ALLOWED_PROPOSED_STATES:
            warnings.append(f"corrections[{index}] invalid proposed_state={proposed_state}")
            continue
        if anomaly_route not in ALLOWED_ANOMALY_ROUTES:
            warnings.append(f"corrections[{index}] invalid anomaly_route={anomaly_route}")
            continue
        if sample_window not in ALLOWED_SAMPLE_WINDOWS:
            warnings.append(f"corrections[{index}] invalid sample_window={sample_window}")
            continue
        parsed.append(item)
    return ("parsed" if parsed or not warnings else "parsed_empty"), parsed, warnings


def _guard_ai_proposal(candidate: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    proposed_state = proposal.get("proposed_state")
    proposed_value = proposal.get("proposed_value")
    anomaly_route = proposal.get("anomaly_route")
    effective_state = candidate.get("calibration_state")
    effective_value = candidate.get("current_value")
    guard_accepted = False
    reject_reason = "proposal_only_no_runtime_apply"
    clamped = False

    if proposed_state in {"adjust_up", "adjust_down", "hold", "hold_sample", "freeze"}:
        effective_state = proposed_state
        guard_accepted = True
        reject_reason = None

    bounds = candidate.get("bounds")
    if proposed_value not in (None, ""):
        numeric_value = _safe_float(proposed_value, default=None)
        if isinstance(bounds, dict) and numeric_value is not None:
            min_value = _safe_float(bounds.get("min"), default=None)
            max_value = _safe_float(bounds.get("max"), default=None)
            effective_value = numeric_value
            if min_value is not None and numeric_value < min_value:
                effective_value = min_value
                clamped = True
            if max_value is not None and numeric_value > max_value:
                effective_value = max_value
                clamped = True
            guard_accepted = True
            reject_reason = None
        elif proposed_value is not None:
            reject_reason = "missing_numeric_bounds_for_value_proposal"
            guard_accepted = False

    return {
        "guard_accepted": bool(guard_accepted),
        "guard_reject_reason": reject_reason,
        "effective_state": effective_state,
        "effective_value": effective_value,
        "clamped": clamped,
        "anomaly_route": anomaly_route,
        "route_action": "workorder_proposal_only",
        "runtime_change": False,
    }


def _build_ai_review_input_context(audit_report: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "date": audit_report.get("date"),
        "authority": "proposal_only",
        "runtime_change": False,
        "policy": audit_report.get("policy"),
        "lifecycle_summary": {
            "model_selection": audit_report.get("model_selection"),
            "recommendation_csv": audit_report.get("recommendation_csv"),
            "db_lifecycle": audit_report.get("db_lifecycle"),
            "observation_axis_summary": audit_report.get("observation_axis_summary"),
            "group_unique_counts": (audit_report.get("lifecycle_events") or {}).get("group_unique_counts"),
            "gatekeeper_actions": (audit_report.get("lifecycle_events") or {}).get("gatekeeper_actions"),
        },
        "calibration_candidates": candidates,
    }


def _build_openai_review_instructions() -> str:
    return (
        "You are the swing-trading lifecycle threshold reviewer and improvement proposer.\n"
        "Your authority is proposal-only. Do not command runtime/env/code changes, broker orders, restarts, "
        "or intraday threshold mutation.\n"
        "Review selection, DB load, entry, holding, scale-in, exit, and attribution evidence.\n"
        "Return only strict JSON using threshold_ai_correction_v1.\n"
        "Use proposed_state values only from adjust_up, adjust_down, hold, hold_sample, or freeze.\n"
        "Use anomaly_route values only from threshold_candidate, incident, instrumentation_gap, or normal_drift.\n"
        "Preserve family ids, enum labels, ticker names, and raw evidence exactly.\n"
        "Korean glossary: selection=종목선정, entry=진입, holding=보유, exit=청산, "
        "AVG_DOWN=물타기, PYRAMID=불타기, 수급=order-flow pressure, 호가=quote/order book.\n"
    )


def _call_openai_swing_threshold_review(input_context: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.daily_threshold_cycle_report import (
            _extract_openai_response_text,
            _load_threshold_ai_openai_keys,
            _threshold_ai_openai_model_sequence,
        )
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}"}

    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured"}

    errors: list[dict[str, str]] = []
    model_sequence = _threshold_ai_openai_model_sequence()
    for model_index, model_name in enumerate(model_sequence, start=1):
        for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
            try:
                client = OpenAI(api_key=api_key)
                response = client.responses.create(
                    model=model_name,
                    instructions=_build_openai_review_instructions(),
                    input=json.dumps(input_context, ensure_ascii=False, indent=2, default=str),
                    text={
                        "format": build_openai_response_text_format("threshold_ai_correction_v1"),
                        "verbosity": "low",
                    },
                    reasoning={"effort": "medium"},
                    store=False,
                    metadata={
                        "endpoint_name": "swing_threshold_ai_review",
                        "schema_name": "threshold_ai_correction_v1",
                        "report_type": "swing_threshold_ai_review",
                    },
                    timeout=180,
                )
                return _extract_openai_response_text(response), {
                    "provider": "openai",
                    "status": "success",
                    "key_name": key_name,
                    "attempt_index": attempt_index,
                    "model_index": model_index,
                    "attempted_keys": len(api_keys),
                    "attempted_models": model_sequence,
                    "model": model_name,
                    "schema_name": "threshold_ai_correction_v1",
                    "reasoning_effort": "medium",
                }
            except RateLimitError as exc:
                errors.append({"key_name": key_name, "model": model_name, "error": str(exc)})
            except Exception as exc:
                errors.append({"key_name": key_name, "model": model_name, "error": str(exc)})
    return None, {
        "provider": "openai",
        "status": "failed",
        "attempted_keys": len(api_keys),
        "attempted_models": model_sequence,
        "schema_name": "threshold_ai_correction_v1",
        "reasoning_effort": "medium",
        "errors": errors,
    }


def build_swing_threshold_ai_review_report(
    audit_report: dict[str, Any],
    *,
    ai_raw_response: Any | None = None,
    ai_provider_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidates = build_swing_threshold_candidates(audit_report)
    ai_status, proposals, parse_warnings = _parse_ai_review_response(ai_raw_response)
    proposals_by_family = {str(item.get("family")): item for item in proposals}

    items: list[dict[str, Any]] = []
    for candidate in candidates:
        family = str(candidate.get("family") or "")
        proposal_item = proposals_by_family.get(family)
        if proposal_item:
            proposal = proposal_item.get("correction_proposal") or {}
            guard_decision = _guard_ai_proposal(candidate, proposal)
            ai_review_state = proposal_item.get("ai_review_state")
            correction_reason = proposal_item.get("correction_reason") or ""
            required_evidence = proposal_item.get("required_evidence") or []
            risk_flags = proposal_item.get("risk_flags") or []
            anomaly_type = proposal_item.get("anomaly_type") or "-"
        else:
            guard_decision = {
                "guard_accepted": False,
                "guard_reject_reason": "ai_unavailable" if ai_status == "unavailable" else "ai_proposal_missing_for_family",
                "effective_state": candidate.get("calibration_state"),
                "effective_value": candidate.get("current_value"),
                "clamped": False,
                "anomaly_route": None,
                "route_action": "deterministic_only",
                "runtime_change": False,
            }
            ai_review_state = "unavailable" if ai_status == "unavailable" else "insufficient_context"
            correction_reason = ""
            required_evidence = []
            risk_flags = []
            anomaly_type = "-"
        items.append(
            {
                "family": family,
                "lifecycle_stage": candidate.get("lifecycle_stage"),
                "anomaly_type": anomaly_type,
                "ai_review_state": ai_review_state,
                "correction_proposal": {
                    "ai_proposed_state": (proposal_item or {}).get("correction_proposal", {}).get("proposed_state")
                    if proposal_item
                    else None,
                    "ai_proposed_value": (proposal_item or {}).get("correction_proposal", {}).get("proposed_value")
                    if proposal_item
                    else None,
                    "ai_anomaly_route": (proposal_item or {}).get("correction_proposal", {}).get("anomaly_route")
                    if proposal_item
                    else None,
                    "ai_sample_window": (proposal_item or {}).get("correction_proposal", {}).get("sample_window")
                    if proposal_item
                    else None,
                },
                "correction_reason": correction_reason,
                "required_evidence": required_evidence,
                "risk_flags": risk_flags,
                "guard_decision": guard_decision,
                "guard_accepted": bool(guard_decision.get("guard_accepted")),
                "guard_reject_reason": guard_decision.get("guard_reject_reason"),
                "deterministic_state": candidate.get("calibration_state"),
                "deterministic_value": candidate.get("recommended_value"),
                "source_metrics": candidate.get("source_metrics"),
                "allowed_runtime_apply": False,
                "runtime_change": False,
            }
        )

    return {
        "schema_version": THRESHOLD_REVIEW_SCHEMA_VERSION,
        "report_type": "swing_threshold_ai_review",
        "date": audit_report.get("date"),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "owner": SWING_LIFECYCLE_OWNER,
        "runtime_change": False,
        "ai_status": ai_status,
        "ai_provider_status": ai_provider_status or {"provider": "none", "status": "not_requested"},
        "parse_warnings": parse_warnings,
        "policy": {
            "authority": "proposal_only",
            "final_source_of_truth": "deterministic_guard_and_manual_workorder",
            "runtime_change": False,
            "forbidden": [
                "env/code/runtime direct change",
                "intraday threshold mutation",
                "safety guard bypass",
                "broker order submission",
                "single-case live enable finalization",
            ],
        },
        "ai_input_context": _build_ai_review_input_context(audit_report, candidates),
        "candidate_count": len(candidates),
        "items": items,
    }


def _order(
    *,
    order_id: str,
    title: str,
    lifecycle_stage: str,
    target_subsystem: str,
    priority: int,
    route: str,
    mapped_family: str | None,
    intent: str,
    expected_ev_effect: str,
    files_likely_touched: list[str],
    acceptance_tests: list[str],
    evidence: list[str],
    improvement_type: str,
) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "title": title,
        "lifecycle_stage": lifecycle_stage,
        "target_subsystem": target_subsystem,
        "priority": priority,
        "route": route,
        "mapped_family": mapped_family,
        "threshold_family": mapped_family,
        "intent": intent,
        "expected_ev_effect": expected_ev_effect,
        "files_likely_touched": files_likely_touched,
        "acceptance_tests": acceptance_tests,
        "evidence": evidence,
        "improvement_type": improvement_type,
        "runtime_effect": False,
        "runtime_effect_type": "report_only_or_feature_flag_off",
        "next_postclose_metric": expected_ev_effect,
    }


def build_swing_improvement_automation_report(
    audit_report: dict[str, Any],
    threshold_ai_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    date_key = str(audit_report.get("date") or "")
    model = audit_report.get("model_selection") or {}
    csv = audit_report.get("recommendation_csv") or {}
    db = audit_report.get("db_lifecycle") or {}
    events = audit_report.get("lifecycle_events") or {}
    raw = events.get("raw_counts") or {}
    unique = events.get("unique_record_counts") or {}
    axis_summary = audit_report.get("observation_axis_summary") or {}

    findings: list[dict[str, Any]] = []
    orders: list[dict[str, Any]] = []
    auto_family_candidates: list[dict[str, Any]] = []

    if int(axis_summary.get("instrumentation_gap_count") or 0) > 0:
        findings.append(
            {
                "finding_id": "swing_lifecycle_observation_coverage",
                "title": "swing lifecycle observation coverage",
                "confidence": "consensus",
                "route": "instrumentation_order",
                "mapped_family": None,
                "target_subsystem": "runtime_instrumentation",
                "lifecycle_stage": "full_lifecycle",
            }
        )
        orders.append(
            _order(
                order_id="order_swing_lifecycle_observation_coverage",
                title="swing lifecycle observation coverage",
                lifecycle_stage="full_lifecycle",
                target_subsystem="runtime_instrumentation",
                priority=1,
                route="instrumentation_order",
                mapped_family=None,
                intent="Close missing lifecycle fields for selection-entry-holding-scale-in-exit attribution.",
                expected_ev_effect="instrumentation_gap_count decreases and stage field coverage increases.",
                files_likely_touched=[
                    "src/engine/swing_lifecycle_audit.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/sniper_scale_in.py",
                ],
                acceptance_tests=["pytest swing lifecycle audit tests", "pipeline event field coverage smoke"],
                evidence=[f"instrumentation_gap_count={axis_summary.get('instrumentation_gap_count')}"],
                improvement_type="instrumentation",
            )
        )

    if int(model.get("selected_count") or 0) <= 0 or int(csv.get("csv_rows") or 0) <= 0:
        findings.append(
            {
                "finding_id": "swing_selection_model_floor_review",
                "title": "swing selection model floor review",
                "confidence": "consensus",
                "route": "existing_family",
                "mapped_family": "swing_model_floor",
                "target_subsystem": "swing_selection",
                "lifecycle_stage": "selection",
            }
        )
        orders.append(
            _order(
                order_id="order_swing_selection_model_floor_review",
                title="swing selection model floor review",
                lifecycle_stage="selection",
                target_subsystem="swing_selection",
                priority=2,
                route="existing_family",
                mapped_family="swing_model_floor",
                intent="Keep model floor and candidate count observable when official swing recommendations drop to zero.",
                expected_ev_effect="selected_count and safe_pool_count recover without FALLBACK_DIAGNOSTIC contamination.",
                files_likely_touched=[
                    "src/model/recommend_daily_v2.py",
                    "src/model/common_v2.py",
                    "src/engine/swing_lifecycle_audit.py",
                ],
                acceptance_tests=["pytest swing model selection funnel tests"],
                evidence=[f"selected_count={model.get('selected_count')}", f"csv_rows={csv.get('csv_rows')}"],
                improvement_type="threshold_family_input",
            )
        )

    if int(csv.get("csv_rows") or 0) > 0 and int(db.get("db_rows") or 0) <= 0:
        findings.append(
            {
                "finding_id": "swing_recommendation_db_load_gap",
                "title": "swing recommendation DB load gap",
                "confidence": "consensus",
                "route": "instrumentation_order",
                "mapped_family": None,
                "target_subsystem": "runtime_instrumentation",
                "lifecycle_stage": "db_load",
            }
        )
        orders.append(
            _order(
                order_id="order_swing_recommendation_db_load_gap",
                title="swing recommendation DB load gap",
                lifecycle_stage="db_load",
                target_subsystem="runtime_instrumentation",
                priority=2,
                route="instrumentation_order",
                mapped_family=None,
                intent="Separate recommendation generation from DB ingestion failure.",
                expected_ev_effect="csv_rows and db_rows no longer diverge without a warning.",
                files_likely_touched=["src/scanners/final_ensemble_scanner.py", "src/engine/swing_lifecycle_audit.py"],
                acceptance_tests=["pytest swing funnel/report tests"],
                evidence=[f"csv_rows={csv.get('csv_rows')}", f"db_rows={db.get('db_rows')}"],
                improvement_type="instrumentation",
            )
        )

    gatekeeper_reject_unique = int(unique.get("blocked_gatekeeper_reject", 0) or 0)
    if gatekeeper_reject_unique > 0:
        findings.append(
            {
                "finding_id": "swing_gatekeeper_reject_threshold_review",
                "title": "swing gatekeeper reject threshold review",
                "confidence": "consensus",
                "route": "existing_family",
                "mapped_family": "swing_gatekeeper_accept_reject",
                "target_subsystem": "swing_entry",
                "lifecycle_stage": "entry",
            }
        )
        orders.append(
            _order(
                order_id="order_swing_gatekeeper_reject_threshold_review",
                title="swing gatekeeper reject threshold review",
                lifecycle_stage="entry",
                target_subsystem="swing_entry",
                priority=3,
                route="existing_family",
                mapped_family="swing_gatekeeper_accept_reject",
                intent="Review gatekeeper reject/pass distribution before loosening any entry guard.",
                expected_ev_effect="gatekeeper reject/pass, submitted/simulated, and post-entry outcomes are attributable by family.",
                files_likely_touched=[
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/swing_lifecycle_audit.py",
                ],
                acceptance_tests=["pytest swing lifecycle audit tests", "pytest state handler fast signatures"],
                evidence=[f"blocked_gatekeeper_reject_unique={gatekeeper_reject_unique}"],
                improvement_type="threshold_family_input",
            )
        )

    if int(raw.get("market_regime_block", 0) or 0) > 0:
        findings.append(
            {
                "finding_id": "swing_market_regime_sensitivity_review",
                "title": "swing market regime sensitivity review",
                "confidence": "consensus",
                "route": "existing_family",
                "mapped_family": "swing_market_regime_sensitivity",
                "target_subsystem": "swing_entry",
                "lifecycle_stage": "entry",
            }
        )
        orders.append(
            _order(
                order_id="order_swing_market_regime_sensitivity_review",
                title="swing market regime sensitivity review",
                lifecycle_stage="entry",
                target_subsystem="swing_entry",
                priority=4,
                route="existing_family",
                mapped_family="swing_market_regime_sensitivity",
                intent="Attribute market-regime hard blocks before proposing sensitivity changes.",
                expected_ev_effect="market_regime_block/pass and missed-entry outcome are visible in the next audit.",
                files_likely_touched=["src/engine/sniper_state_handlers.py", "src/engine/swing_lifecycle_audit.py"],
                acceptance_tests=["pytest swing lifecycle audit tests"],
                evidence=[f"market_regime_block_raw={raw.get('market_regime_block')}"],
                improvement_type="threshold_family_input",
            )
        )

    findings.append(
        {
            "finding_id": "swing_ai_contract_structured_output_eval",
            "title": "swing AI contract structured output eval",
            "confidence": "consensus",
            "route": "auto_family_candidate",
            "mapped_family": None,
            "target_subsystem": "swing_ai_contract",
            "lifecycle_stage": "ai_contract",
        }
    )
    auto_family_candidates.append(
        {
            "family_id": "swing_ai_contract_structured_output_eval",
            "implementation_order_id": "order_swing_ai_contract_structured_output_eval",
            "allowed_runtime_apply": False,
            "runtime_change": False,
        }
    )
    orders.append(
        _order(
            order_id="order_swing_ai_contract_structured_output_eval",
            title="swing AI contract structured output eval",
            lifecycle_stage="ai_contract",
            target_subsystem="swing_ai_contract",
            priority=5,
            route="auto_family_candidate",
            mapped_family=None,
            intent="Replay Korean prompt vs English-control prompt vs strict schema prompt before adopting a swing AI contract.",
            expected_ev_effect="schema_valid_rate, decision disagreement, latency, and cost are reported before model/prompt change.",
            files_likely_touched=[
                "src/engine/ai_engine.py",
                "src/engine/ai_engine_openai.py",
                "src/engine/ai_response_contracts.py",
            ],
            acceptance_tests=["pytest OpenAI transport/schema tests", "pytest swing lifecycle audit tests"],
            evidence=[issue["issue_id"] for issue in AI_CONTRACT_ISSUES],
            improvement_type="ai_contract_eval",
        )
    )

    if int((events.get("group_unique_counts") or {}).get("scale_in", 0) or 0) <= 0:
        findings.append(
            {
                "finding_id": "swing_scale_in_avg_down_pyramid_sample_gap",
                "title": "swing scale-in AVG_DOWN/PYRAMID sample gap",
                "confidence": "solo",
                "route": "auto_family_candidate",
                "mapped_family": None,
                "target_subsystem": "swing_scale_in",
                "lifecycle_stage": "scale_in",
            }
        )
        auto_family_candidates.append(
            {
                "family_id": "swing_scale_in_avg_down_pyramid_observation",
                "implementation_order_id": "order_swing_scale_in_avg_down_pyramid_observation",
                "allowed_runtime_apply": False,
                "runtime_change": False,
            }
        )
        orders.append(
            _order(
                order_id="order_swing_scale_in_avg_down_pyramid_observation",
                title="swing scale-in AVG_DOWN/PYRAMID observation",
                lifecycle_stage="scale_in",
                target_subsystem="swing_scale_in",
                priority=6,
                route="auto_family_candidate",
                mapped_family=None,
                intent="Keep AVG_DOWN/PYRAMID as observation/proposal until samples and guards are closed.",
                expected_ev_effect="scale_in group coverage and add_type/post_add outcome fields appear in lifecycle audit.",
                files_likely_touched=["src/engine/sniper_scale_in.py", "src/engine/sniper_state_handlers.py"],
                acceptance_tests=["pytest sniper scale-in tests", "pytest swing lifecycle audit tests"],
                evidence=["scale_in_unique_records=0"],
                improvement_type="lifecycle_logic_observation",
            )
        )

    return {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "report_type": "swing_improvement_automation",
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "owner": SWING_LIFECYCLE_OWNER,
        "runtime_change": False,
        "policy": {
            "runtime_patch_automation": False,
            "user_intervention_point": "generated code improvement workorder is pasted into Codex manually",
            "threshold_ai_review_authority": "proposal_only",
        },
        "source_reports": {
            "swing_lifecycle_audit": str(SWING_LIFECYCLE_AUDIT_DIR / f"swing_lifecycle_audit_{date_key}.json"),
            "swing_threshold_ai_review": str(
                SWING_THRESHOLD_AI_REVIEW_DIR / f"swing_threshold_ai_review_{date_key}.json"
            ),
        },
        "ev_report_summary": {
            "swing_lifecycle_audit_available": True,
            "threshold_ai_status": (threshold_ai_review or {}).get("ai_status"),
            "instrumentation_gap_count": axis_summary.get("instrumentation_gap_count"),
            "hold_sample_count": axis_summary.get("hold_sample_count"),
        },
        "consensus_findings": [item for item in findings if item.get("confidence") != "solo"],
        "solo_findings": [item for item in findings if item.get("confidence") == "solo"],
        "auto_family_candidates": auto_family_candidates,
        "code_improvement_orders": orders,
    }


def render_swing_lifecycle_audit_markdown(report: dict[str, Any]) -> str:
    model = report.get("model_selection") or {}
    csv = report.get("recommendation_csv") or {}
    db = report.get("db_lifecycle") or {}
    events = report.get("lifecycle_events") or {}
    axis_summary = report.get("observation_axis_summary") or {}
    lines = [
        f"# Swing Lifecycle Audit - {report.get('date')}",
        "",
        f"- owner: `{report.get('owner')}`",
        "- runtime_change: `false`",
        f"- selected_count: `{model.get('selected_count')}`",
        f"- csv_rows: `{csv.get('csv_rows')}`",
        f"- db_rows: `{db.get('db_rows')}`",
        f"- entered_rows: `{db.get('entered_rows')}`",
        f"- completed_rows: `{db.get('completed_rows')}`",
        f"- submitted_unique_records: `{events.get('submitted_unique_records')}`",
        f"- simulated_order_unique_records: `{events.get('simulated_order_unique_records')}`",
        f"- observation_axis_status: `{axis_summary.get('status_counts')}`",
        "",
        "## Lifecycle Funnel",
        "",
        "| group | raw | unique_records |",
        "| --- | ---: | ---: |",
    ]
    group_raw = events.get("group_raw_counts") or {}
    group_unique = events.get("group_unique_counts") or {}
    for group in ("entry", "holding", "scale_in", "exit", "other"):
        lines.append(f"| `{group}` | {group_raw.get(group, 0)} | {group_unique.get(group, 0)} |")

    lines.extend(["", "## Key Stages", "", "| stage | raw | unique_records |", "| --- | ---: | ---: |"])
    raw = events.get("raw_counts") or {}
    unique = events.get("unique_record_counts") or {}
    for stage in sorted(raw):
        if raw.get(stage, 0) or unique.get(stage, 0):
            lines.append(f"| `{stage}` | {raw.get(stage, 0)} | {unique.get(stage, 0)} |")

    lines.extend(["", "## Observation Axes", "", "| axis | stage | family | sample | status |", "| --- | --- | --- | ---: | --- |"])
    for axis in report.get("observation_axes") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{axis.get('axis_id')}`",
                    f"`{axis.get('lifecycle_stage')}`",
                    f"`{axis.get('threshold_family')}`",
                    str(axis.get("sample_count") or 0),
                    f"`{axis.get('status')}`",
                ]
            )
            + " |"
        )

    lines.extend(["", "## AI Contract Audit", ""])
    for issue in (report.get("ai_contract_audit") or {}).get("contract_issues") or []:
        lines.append(
            f"- `{issue.get('issue_id')}` stage=`{issue.get('lifecycle_stage')}` severity=`{issue.get('severity')}`: {issue.get('reason')}"
        )
    lines.append("")
    return "\n".join(lines)


def render_swing_threshold_ai_review_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Swing Threshold AI Review - {report.get('date')}",
        "",
        f"- AI status: `{report.get('ai_status')}`",
        "- Authority: proposal-only; deterministic guard and manual workorder remain the source of truth.",
        "- Runtime change: `false`",
        "",
        "| family | stage | deterministic | ai_state | proposal | guard |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report.get("items") or []:
        proposal = item.get("correction_proposal") or {}
        guard = item.get("guard_decision") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item.get('family')}`",
                    f"`{item.get('lifecycle_stage')}`",
                    f"`{item.get('deterministic_state')}`",
                    f"`{item.get('ai_review_state')}`",
                    f"state={proposal.get('ai_proposed_state') or '-'}, value={proposal.get('ai_proposed_value')}",
                    f"accepted={guard.get('guard_accepted')}, reason={guard.get('guard_reject_reason') or '-'}",
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def render_swing_improvement_automation_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Swing Improvement Automation - {report.get('date')}",
        "",
        "- Runtime change: `false`",
        "- Generated orders are inputs for `build_code_improvement_workorder`; implementation is manual.",
        "",
        "## Orders",
        "",
        "| order_id | stage | subsystem | route | family | priority |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for order in report.get("code_improvement_orders") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{order.get('order_id')}`",
                    f"`{order.get('lifecycle_stage')}`",
                    f"`{order.get('target_subsystem')}`",
                    f"`{order.get('route')}`",
                    f"`{order.get('mapped_family') or '-'}`",
                    str(order.get("priority")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_swing_lifecycle_outputs(
    target_date: str | date | datetime,
    *,
    output_root: str | Path | None = None,
    ai_review_provider: str = "none",
    ai_raw_response: Any | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    audit = build_swing_lifecycle_audit_report(date_key, **kwargs)
    candidates = build_swing_threshold_candidates(audit)
    provider_status = {"provider": "none", "status": "not_requested"}
    raw_response = ai_raw_response
    if raw_response is None and str(ai_review_provider or "none").strip().lower() == "openai":
        raw_response, provider_status = _call_openai_swing_threshold_review(
            _build_ai_review_input_context(audit, candidates)
        )
    elif raw_response is not None:
        provider_status = {"provider": "injected", "status": "provided"}
    threshold_review = build_swing_threshold_ai_review_report(
        audit,
        ai_raw_response=raw_response,
        ai_provider_status=provider_status,
    )
    automation = build_swing_improvement_automation_report(audit, threshold_review)

    root = Path(output_root) if output_root is not None else Path(DATA_DIR) / "report"
    audit_dir = root / "swing_lifecycle_audit"
    review_dir = root / "swing_threshold_ai_review"
    automation_dir = root / "swing_improvement_automation"
    for directory in (audit_dir, review_dir, automation_dir):
        directory.mkdir(parents=True, exist_ok=True)

    audit_json = audit_dir / f"swing_lifecycle_audit_{date_key}.json"
    audit_md = audit_dir / f"swing_lifecycle_audit_{date_key}.md"
    review_json = review_dir / f"swing_threshold_ai_review_{date_key}.json"
    review_md = review_dir / f"swing_threshold_ai_review_{date_key}.md"
    automation_json = automation_dir / f"swing_improvement_automation_{date_key}.json"
    automation_md = automation_dir / f"swing_improvement_automation_{date_key}.md"

    audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    audit_md.write_text(render_swing_lifecycle_audit_markdown(audit), encoding="utf-8")
    review_json.write_text(json.dumps(threshold_review, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    review_md.write_text(render_swing_threshold_ai_review_markdown(threshold_review), encoding="utf-8")
    automation_json.write_text(json.dumps(automation, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    automation_md.write_text(render_swing_improvement_automation_markdown(automation), encoding="utf-8")

    paths = {
        "swing_lifecycle_audit_json": str(audit_json),
        "swing_lifecycle_audit_markdown": str(audit_md),
        "swing_threshold_ai_review_json": str(review_json),
        "swing_threshold_ai_review_markdown": str(review_md),
        "swing_improvement_automation_json": str(automation_json),
        "swing_improvement_automation_markdown": str(automation_md),
    }
    audit["paths"] = paths
    threshold_review["paths"] = paths
    automation["paths"] = paths
    return {"audit": audit, "threshold_ai_review": threshold_review, "automation": automation, "paths": paths}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build swing lifecycle audit and improvement automation reports.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument(
        "--ai-review-provider",
        default="none",
        choices=["none", "openai"],
        help="Optional swing threshold AI reviewer provider. Missing keys degrade to unavailable report.",
    )
    args = parser.parse_args(argv)
    outputs = write_swing_lifecycle_outputs(args.target_date, ai_review_provider=args.ai_review_provider)
    print(json.dumps(outputs["paths"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
