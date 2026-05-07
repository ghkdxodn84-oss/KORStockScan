"""Intraday HOLD/EXIT bottleneck sentinel.

This module is report-only. It reads structured holding pipeline events and
saved observation reports, classifies HOLD/EXIT anomalies, writes artifacts,
and optionally notifies the admin Telegram chat.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from urllib import parse, request

from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH
from src.utils.market_day import is_krx_trading_day


IGNORED_STOCK_NAMES = {"TEST", "DUMMY", "MOCK"}
DEFAULT_WINDOWS = (5, 10, 30)
SESSION_START = time(9, 0)
SENTINEL_END = time(15, 30)
REPORT_DIRNAME = "holding_exit_sentinel"
HOLDING_PIPELINE = "HOLDING_PIPELINE"
FORBIDDEN_AUTOMATIONS = [
    "auto_sell",
    "holding_threshold_relaxation",
    "holding_flow_override_mutation",
    "ai_cache_ttl_mutation",
    "bot_restart",
]


@dataclass(frozen=True)
class PipelineEvent:
    emitted_at: datetime
    pipeline: str
    stage: str
    stock_name: str
    stock_code: str
    record_id: str
    fields: dict[str, str]


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _observation_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "monitor_snapshots" / f"holding_exit_observation_{target_date}.json"


def _report_dir() -> Path:
    return DATA_DIR / "report" / REPORT_DIRNAME


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_iso_datetime(value: str) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_target_date(target_date: str) -> date:
    return datetime.strptime(target_date, "%Y-%m-%d").date()


def _parse_as_of(target_date: str, as_of: str | None) -> datetime | None:
    text = _safe_str(as_of)
    if not text:
        return None
    parsed = _parse_iso_datetime(text)
    if parsed is not None:
        return parsed
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(f"{target_date} {text}", f"%Y-%m-%d {fmt}")
        except ValueError:
            continue
    raise ValueError(f"invalid --as-of value: {as_of}")


def _is_ignored_event(payload: dict[str, Any]) -> bool:
    return _safe_str(payload.get("stock_name")).upper() in IGNORED_STOCK_NAMES


def load_pipeline_events(target_date: str) -> list[PipelineEvent]:
    path = _pipeline_events_path(target_date)
    if not path.exists():
        return []
    events: list[PipelineEvent] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if _safe_str(payload.get("event_type")) != "pipeline_event":
                continue
            if _safe_str(payload.get("pipeline")) != HOLDING_PIPELINE:
                continue
            if _is_ignored_event(payload):
                continue
            emitted_at = _parse_iso_datetime(_safe_str(payload.get("emitted_at")))
            if emitted_at is None:
                continue
            raw_fields = payload.get("fields") or {}
            fields = {str(k): _safe_str(v) for k, v in raw_fields.items()}
            record_id = payload.get("record_id")
            if record_id in (None, "", 0):
                record_id = fields.get("id") or ""
            events.append(
                PipelineEvent(
                    emitted_at=emitted_at,
                    pipeline=_safe_str(payload.get("pipeline")),
                    stage=_safe_str(payload.get("stage")),
                    stock_name=_safe_str(payload.get("stock_name")),
                    stock_code=_safe_str(payload.get("stock_code"))[:6],
                    record_id=_safe_str(record_id),
                    fields=fields,
                )
            )
    events.sort(key=lambda event: event.emitted_at)
    return events


def load_observation_report(target_date: str) -> dict[str, Any] | None:
    path = _observation_path(target_date)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def previous_trading_day_with_events(target_date: str, *, max_lookback_days: int = 10) -> str | None:
    current = _parse_target_date(target_date)
    for offset in range(1, max_lookback_days + 1):
        candidate = current - timedelta(days=offset)
        if not is_krx_trading_day(candidate):
            continue
        candidate_text = candidate.isoformat()
        if _pipeline_events_path(candidate_text).exists():
            return candidate_text
    return None


def _attempt_key(event: PipelineEvent) -> str:
    if event.record_id:
        return f"id:{event.record_id}"
    if event.stock_code:
        return f"code:{event.stock_code}"
    return f"name:{event.stock_name}"


def _ratio(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 1) if denominator else 0.0


def _count_cache_miss(events: list[PipelineEvent]) -> int:
    return sum(1 for event in events if event.stage == "ai_holding_review" and event.fields.get("ai_cache") == "miss")


def _count_parse_fail(events: list[PipelineEvent]) -> int:
    return sum(
        1
        for event in events
        if event.stage in {"ai_holding_review", "holding_flow_override_review"}
        and event.fields.get("ai_parse_fail") in {"1", "True", "true", "YES", "yes"}
    )


def _max_field(events: list[PipelineEvent], stage: str, field: str) -> float:
    values = [_safe_float(event.fields.get(field), 0.0) for event in events if event.stage == stage]
    return max(values) if values else 0.0


TERMINAL_HOLDING_STAGES = {"sell_completed"}
ACTIVE_HOLDING_STAGES = {
    "holding_started",
    "position_rebased_after_fill",
    "ai_holding_fast_reuse_band",
    "ai_holding_reuse_bypass",
    "ai_holding_review",
    "ai_holding_skip_unchanged",
    "bad_entry_refined_candidate",
    "exit_signal",
    "holding_flow_override_candidate_cleared",
    "holding_flow_override_defer_exit",
    "holding_flow_override_exit_confirmed",
    "holding_flow_override_force_exit",
    "holding_flow_override_review",
    "reversal_add_blocked_reason",
    "reversal_add_gate_blocked",
    "scale_in_price_guard_block",
    "scale_in_qty_block",
    "sell_order_sent",
    "soft_stop_expert_shadow",
    "soft_stop_micro_grace",
    "stat_action_decision_snapshot",
}


def _active_holding_keys(events: list[PipelineEvent]) -> set[str]:
    last_by_key: dict[str, PipelineEvent] = {}
    for event in events:
        key = _attempt_key(event)
        if not key:
            continue
        last_by_key[key] = event
    return {
        key
        for key, event in last_by_key.items()
        if event.stage in ACTIVE_HOLDING_STAGES and event.stage not in TERMINAL_HOLDING_STAGES
    }


def _stage_reason_top(events: list[PipelineEvent]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for event in events:
        if event.stage == "holding_flow_override_defer_exit":
            key = f"flow유예:{event.fields.get('exit_rule') or '-'}"
        elif event.stage == "exit_signal":
            key = f"청산신호:{event.fields.get('exit_rule') or event.fields.get('reason') or '-'}"
        elif event.stage == "ai_holding_review":
            key = f"AI보유감시:cache_{event.fields.get('ai_cache') or '-'}"
        elif event.stage == "soft_stop_micro_grace":
            key = "soft_stop_grace"
        elif event.stage in {"sell_order_sent", "sell_completed"}:
            key = event.stage
        else:
            continue
        counter[key] += 1
    return [{"label": label, "count": count} for label, count in counter.most_common(10)]


def _summarize_events(events: list[PipelineEvent], *, start_at: datetime, end_at: datetime) -> dict[str, Any]:
    scoped = [event for event in events if start_at <= event.emitted_at <= end_at]
    stage_events = Counter(event.stage for event in scoped)
    stage_unique = {
        stage: len({_attempt_key(event) for event in scoped if event.stage == stage})
        for stage in sorted(set(stage_events))
    }
    exit_signal = int(stage_unique.get("exit_signal", 0) or 0)
    sell_sent = int(stage_unique.get("sell_order_sent", 0) or 0)
    sell_completed = int(stage_unique.get("sell_completed", 0) or 0)
    flow_defer = int(stage_events.get("holding_flow_override_defer_exit", 0) or 0)
    flow_review = int(stage_events.get("holding_flow_override_review", 0) or 0)
    ai_review = int(stage_events.get("ai_holding_review", 0) or 0)
    cache_miss = _count_cache_miss(scoped)
    active_keys = _active_holding_keys(scoped)
    latest_event_at = scoped[-1].emitted_at.isoformat(timespec="seconds") if scoped else None
    return {
        "start_at": start_at.isoformat(timespec="seconds"),
        "end_at": end_at.isoformat(timespec="seconds"),
        "event_count": len(scoped),
        "latest_event_at": latest_event_at,
        "stage_events": dict(sorted(stage_events.items())),
        "stage_unique": stage_unique,
        "reason_top": _stage_reason_top(scoped),
        "max_defer_worsen_pct": round(_max_field(scoped, "holding_flow_override_defer_exit", "worsen_pct"), 3),
        "max_force_worsen_pct": round(_max_field(scoped, "holding_flow_override_force_exit", "profit_rate"), 3),
        "ai_parse_fail_events": _count_parse_fail(scoped),
        "ratios": {
            "sell_sent_to_exit_signal_unique_pct": _ratio(sell_sent, exit_signal),
            "sell_completed_to_exit_signal_unique_pct": _ratio(sell_completed, exit_signal),
            "flow_defer_to_review_event_pct": _ratio(flow_defer, flow_review),
            "ai_cache_miss_pct": _ratio(cache_miss, ai_review),
        },
        "unique_symbols": {
            "holding_started": len({_attempt_key(event) for event in scoped if event.stage == "holding_started"}),
            "exit_signal": exit_signal,
            "sell_order_sent": sell_sent,
            "sell_completed": sell_completed,
            "active_holding": len(active_keys),
        },
    }


def _same_time_on_date(target_date: str, source: datetime) -> datetime:
    return datetime.combine(_parse_target_date(target_date), source.time())


def _observation_metrics(observation: dict[str, Any] | None) -> dict[str, Any]:
    if not observation:
        return {}
    soft_stop = observation.get("soft_stop_rebound") or {}
    trailing = {}
    for item in observation.get("exit_rule_quality") or []:
        if item.get("exit_rule") == "scalp_trailing_take_profit":
            trailing = item
            break
    return {
        "soft_stop_total": int(soft_stop.get("total_soft_stop") or 0),
        "soft_stop_rebound_above_sell_10m_rate": _safe_float(
            soft_stop.get("rebound_above_sell_10m_rate"),
            0.0,
        ),
        "trailing_evaluated": int(trailing.get("evaluated_post_sell") or 0),
        "trailing_missed_upside_rate": _safe_float(trailing.get("missed_upside_rate"), 0.0),
    }


def _classify(summary: dict[str, Any], baseline: dict[str, Any] | None, observation_metrics: dict[str, Any], *, as_of: datetime) -> dict[str, Any]:
    stage_events = summary["stage_events"]
    unique = summary["stage_unique"]
    ratios = summary["ratios"]
    latest = _parse_iso_datetime(_safe_str(summary.get("latest_event_at")))
    stale_sec = int((as_of - latest).total_seconds()) if latest else None
    during_sentinel_hours = SESSION_START <= as_of.time() <= SENTINEL_END

    exit_signal = int(unique.get("exit_signal", 0) or 0)
    sell_sent = int(unique.get("sell_order_sent", 0) or 0)
    flow_defer = int(stage_events.get("holding_flow_override_defer_exit", 0) or 0)
    force_exit = int(stage_events.get("holding_flow_override_force_exit", 0) or 0)
    exit_confirmed = int(stage_events.get("holding_flow_override_exit_confirmed", 0) or 0)
    ai_review = int(stage_events.get("ai_holding_review", 0) or 0)
    active_holding = int(summary.get("unique_symbols", {}).get("active_holding", 0) or 0)

    matches: list[str] = []
    reasons: list[str] = []

    if during_sentinel_hours and summary["event_count"] == 0:
        matches.append("RUNTIME_OPS")
        reasons.append("holding pipeline event stream is empty during sentinel hours")
    elif (
        during_sentinel_hours
        and stale_sec is not None
        and stale_sec > 900
        and ai_review > 0
        and active_holding > 0
    ):
        matches.append("RUNTIME_OPS")
        reasons.append("holding pipeline event stream is stale while active holdings remain")

    if exit_signal >= 1 and sell_sent < exit_signal:
        matches.append("SELL_EXECUTION_DROUGHT")
        reasons.append("exit_signal is not fully followed by sell_order_sent")

    if flow_defer >= 3 or force_exit >= 1 or exit_confirmed >= 2:
        matches.append("HOLD_DEFER_DANGER")
        reasons.append("holding_flow_override defer/force/confirm events are elevated")

    if ai_review >= 5 and (
        ratios.get("ai_cache_miss_pct", 0.0) >= 90.0 or summary.get("ai_parse_fail_events", 0) > 0
    ):
        matches.append("AI_HOLDING_OPS")
        reasons.append("AI holding review cache miss or parse failure is elevated")

    if (
        observation_metrics.get("soft_stop_total", 0) >= 5
        and observation_metrics.get("soft_stop_rebound_above_sell_10m_rate", 0.0) >= 70.0
    ):
        matches.append("SOFT_STOP_WHIPSAW")
        reasons.append("soft stop rebound rate is high in saved observation")

    if (
        observation_metrics.get("trailing_evaluated", 0) >= 5
        and observation_metrics.get("trailing_missed_upside_rate", 0.0) >= 30.0
    ):
        matches.append("TRAILING_EARLY_EXIT")
        reasons.append("trailing missed-upside rate is high in saved observation")

    priority = [
        "RUNTIME_OPS",
        "SELL_EXECUTION_DROUGHT",
        "HOLD_DEFER_DANGER",
        "AI_HOLDING_OPS",
        "SOFT_STOP_WHIPSAW",
        "TRAILING_EARLY_EXIT",
    ]
    primary = next((item for item in priority if item in matches), "NORMAL")
    secondary = [item for item in matches if item != primary]
    if primary == "NORMAL":
        reasons.append("no HOLD/EXIT sentinel threshold breached")

    return {
        "primary": primary,
        "secondary": secondary,
        "matches": matches,
        "reasons": reasons,
        "stale_sec": stale_sec,
        "baseline_sell_sent_to_exit_signal_unique_pct": (
            (baseline or {}).get("ratios", {}).get("sell_sent_to_exit_signal_unique_pct")
        ),
        "live_runtime_effect": False,
        "forbidden_automations": FORBIDDEN_AUTOMATIONS,
    }


def _recommend_actions(classification: dict[str, Any]) -> list[str]:
    primary = classification.get("primary")
    if primary == "SELL_EXECUTION_DROUGHT":
        return ["Check sell order receipt/order path before changing exit thresholds."]
    if primary == "HOLD_DEFER_DANGER":
        return ["Review holding_flow_override defer examples and worsen floor evidence."]
    if primary == "AI_HOLDING_OPS":
        return ["Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically."]
    if primary == "SOFT_STOP_WHIPSAW":
        return ["Append soft-stop rebound examples to postclose threshold review."]
    if primary == "TRAILING_EARLY_EXIT":
        return ["Append trailing missed-upside examples to postclose threshold review."]
    if primary == "RUNTIME_OPS":
        return ["Check holding pipeline event freshness; restart only after explicit approval."]
    return ["Continue monitoring; no dynamic action required."]


def build_holding_exit_sentinel_report(
    target_date: str,
    *,
    as_of: datetime | None = None,
    windows_min: tuple[int, ...] = DEFAULT_WINDOWS,
    dry_run: bool = False,
) -> dict[str, Any]:
    events = load_pipeline_events(target_date)
    if as_of is None:
        if dry_run and events:
            as_of = events[-1].emitted_at
        else:
            as_of = datetime.now()

    session_start = datetime.combine(_parse_target_date(target_date), SESSION_START)
    session_summary = _summarize_events(events, start_at=session_start, end_at=as_of)
    windows = {}
    for minutes in sorted(set(windows_min)):
        start_at = max(session_start, as_of - timedelta(minutes=minutes))
        windows[f"{minutes}m"] = _summarize_events(events, start_at=start_at, end_at=as_of)

    baseline_date = previous_trading_day_with_events(target_date)
    baseline_summary = None
    if baseline_date:
        baseline_events = load_pipeline_events(baseline_date)
        baseline_start = datetime.combine(_parse_target_date(baseline_date), SESSION_START)
        baseline_end = _same_time_on_date(baseline_date, as_of)
        baseline_summary = _summarize_events(baseline_events, start_at=baseline_start, end_at=baseline_end)

    observation = load_observation_report(target_date)
    obs_metrics = _observation_metrics(observation)
    classification = _classify(session_summary, baseline_summary, obs_metrics, as_of=as_of)

    return {
        "schema_version": 1,
        "report_type": "holding_exit_sentinel",
        "target_date": target_date,
        "as_of": as_of.isoformat(timespec="seconds"),
        "dry_run": bool(dry_run),
        "policy": {
            "report_only": True,
            "live_runtime_effect": False,
            "allowed_automations": ["json_report", "markdown_report", "telegram_admin_alert", "action_recommendation"],
            "forbidden_automations": FORBIDDEN_AUTOMATIONS,
        },
        "baseline": {"date": baseline_date, "same_time_summary": baseline_summary},
        "current": {"session": session_summary, "windows": windows},
        "observation": {"path": str(_observation_path(target_date)), "metrics": obs_metrics},
        "classification": classification,
        "recommended_actions": _recommend_actions(classification),
    }


def _format_top(items: list[dict[str, Any]], *, limit: int = 5) -> str:
    if not items:
        return "-"
    return ", ".join(f"{item['label']}={item['count']}" for item in items[:limit])


def build_markdown(report: dict[str, Any]) -> str:
    session = report["current"]["session"]
    unique = session["stage_unique"]
    ratios = session["ratios"]
    classification = report["classification"]
    obs = report["observation"]["metrics"]
    lines = [
        f"# HOLD/EXIT Sentinel {report['target_date']}",
        "",
        "## 판정",
        "",
        f"- primary: `{classification['primary']}`",
        f"- secondary: `{', '.join(classification['secondary']) if classification['secondary'] else '-'}`",
        f"- report_only: `{str(report['policy']['report_only']).lower()}`",
        f"- live_runtime_effect: `{str(report['policy']['live_runtime_effect']).lower()}`",
        "",
        "## 근거",
        "",
        f"- as_of: `{report['as_of']}`",
        f"- exit_signal unique: `{unique.get('exit_signal', 0)}`",
        f"- sell_order_sent unique: `{unique.get('sell_order_sent', 0)}`",
        f"- sell_completed unique: `{unique.get('sell_completed', 0)}`",
        f"- sell_sent/exit_signal: `{ratios.get('sell_sent_to_exit_signal_unique_pct', 0.0)}%`",
        f"- flow defer events: `{session['stage_events'].get('holding_flow_override_defer_exit', 0)}`",
        f"- AI holding cache MISS: `{ratios.get('ai_cache_miss_pct', 0.0)}%`",
        f"- soft_stop rebound above sell 10m: `{obs.get('soft_stop_rebound_above_sell_10m_rate', 0.0)}%`",
        f"- trailing missed-upside: `{obs.get('trailing_missed_upside_rate', 0.0)}%`",
        f"- top reasons: `{_format_top(session['reason_top'])}`",
        "",
        "## 금지된 자동변경",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["policy"]["forbidden_automations"])
    lines.extend(["", "## 권고 액션", ""])
    lines.extend(f"- {item}" for item in report["recommended_actions"])
    return "\n".join(lines) + "\n"


def save_report_artifacts(report: dict[str, Any]) -> dict[str, str]:
    target_date = report["target_date"]
    report_dir = _report_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"holding_exit_sentinel_{target_date}.json"
    md_path = report_dir / f"holding_exit_sentinel_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def _classification_label_ko(primary: str, secondary: list[str]) -> str:
    labels = {
        "SELL_EXECUTION_DROUGHT": "매도 주문/체결 병목",
        "HOLD_DEFER_DANGER": "HOLD 유예 악화",
        "SOFT_STOP_WHIPSAW": "soft stop 반등 과다",
        "TRAILING_EARLY_EXIT": "trailing 조기청산",
        "AI_HOLDING_OPS": "AI 보유감시 이상",
        "RUNTIME_OPS": "런타임/이벤트 이상",
        "NORMAL": "정상",
    }
    parts = [labels.get(primary, primary)]
    parts.extend(labels.get(item, item) for item in secondary if item and item != primary)
    return " + ".join(parts)


def _format_as_of_hm(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%H:%M")
    except Exception:
        return value


def build_telegram_message(report: dict[str, Any], artifacts: dict[str, str]) -> str:
    session = report["current"]["session"]
    unique = session["stage_unique"]
    ratios = session["ratios"]
    obs = report["observation"]["metrics"]
    classification = report["classification"]
    primary = classification["primary"]
    secondary = classification.get("secondary") or []
    return "\n".join(
        [
            "[KORStockScan] HOLD/EXIT 이상치",
            f"- 시각: {_format_as_of_hm(report['as_of'])}",
            f"- 판정: {_classification_label_ko(primary, secondary)}",
            (
                "- 전환: "
                f"청산신호 {unique.get('exit_signal', 0)} -> "
                f"매도주문 {unique.get('sell_order_sent', 0)}"
                f"({ratios.get('sell_sent_to_exit_signal_unique_pct', 0.0)}%) -> "
                f"매도완료 {unique.get('sell_completed', 0)}"
            ),
            (
                "- 원인: "
                f"HOLD유예 {session['stage_events'].get('holding_flow_override_defer_exit', 0)}건, "
                f"AI MISS {ratios.get('ai_cache_miss_pct', 0.0)}%, "
                f"softStop반등 {obs.get('soft_stop_rebound_above_sell_10m_rate', 0.0)}%, "
                f"trailing미스 {obs.get('trailing_missed_upside_rate', 0.0)}%"
            ),
            "- 자동조치: 없음",
            f"- 상세: {artifacts.get('markdown', '-')}",
        ]
    )


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    if not config_path.exists():
        return "", ""
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return "", ""
    return _safe_str(config.get("TELEGRAM_TOKEN")), _safe_str(config.get("ADMIN_ID"))


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    with request.urlopen(req, timeout=10) as response:
        response.read()


def _notify_state_path(report: dict[str, Any]) -> Path:
    target_date = _safe_str(report.get("target_date")) or datetime.now().strftime("%Y-%m-%d")
    return _report_dir() / f"holding_exit_sentinel_notify_state_{target_date}.json"


def _notification_signature(report: dict[str, Any]) -> str:
    classification = report.get("classification", {})
    primary = _safe_str(classification.get("primary")) or "NORMAL"
    secondary = sorted(_safe_str(item) for item in (classification.get("secondary") or []) if _safe_str(item))
    return "|".join([primary, ",".join(secondary)])


def _load_notify_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_notify_state(path: Path, report: dict[str, Any], signature: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "target_date": _safe_str(report.get("target_date")),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of": _safe_str(report.get("as_of")),
        "signature": signature,
        "primary": _safe_str((report.get("classification") or {}).get("primary")),
        "secondary": list((report.get("classification") or {}).get("secondary") or []),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def should_notify_admin(report: dict[str, Any]) -> bool:
    classification = report.get("classification", {})
    primary = _safe_str(classification.get("primary"))
    secondary = classification.get("secondary") or []
    return primary != "NORMAL" or bool(secondary)


def maybe_notify_admin(report: dict[str, Any], artifacts: dict[str, str], *, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"enabled": False, "status": "skipped", "reason": "disabled"}
    signature = _notification_signature(report)
    state_path = _notify_state_path(report)
    if not should_notify_admin(report):
        previous = _load_notify_state(state_path)
        if previous.get("signature") != signature:
            _write_notify_state(state_path, report, signature)
        return {"enabled": True, "status": "skipped", "reason": "normal"}
    previous = _load_notify_state(state_path)
    if previous.get("signature") == signature:
        return {"enabled": True, "status": "skipped", "reason": "duplicate_signature"}
    token, admin_id = _load_telegram_config()
    if not token or not admin_id:
        return {"enabled": True, "status": "skipped", "reason": "missing_config"}
    _send_telegram(token, admin_id, build_telegram_message(report, artifacts))
    _write_notify_state(state_path, report, signature)
    return {"enabled": True, "status": "sent", "reason": ""}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build intraday HOLD/EXIT sentinel report.")
    parser.add_argument("--date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--as-of", dest="as_of", default="")
    parser.add_argument("--window-min", dest="window_min", action="append", type=int, default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--notify-admin", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    as_of = _parse_as_of(args.target_date, args.as_of) if args.as_of else None
    windows = tuple(args.window_min) if args.window_min else DEFAULT_WINDOWS
    report = build_holding_exit_sentinel_report(
        args.target_date,
        as_of=as_of,
        windows_min=windows,
        dry_run=bool(args.dry_run),
    )
    artifacts = save_report_artifacts(report)
    notify_result = maybe_notify_admin(report, artifacts, enabled=bool(args.notify_admin and not args.dry_run))
    result = {
        "status": "success",
        "target_date": args.target_date,
        "classification": report["classification"]["primary"],
        "secondary": report["classification"]["secondary"],
        "artifacts": artifacts,
        "notify": notify_result,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.print_json else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
