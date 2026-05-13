"""Report-only panic buying attribution.

The report detects intraday panic buying and buying exhaustion from pipeline
events, separates TP/runner counterfactuals from real order behavior, and routes
future runner TP work to approval-required candidates. It never mutates runtime
thresholds or order behavior.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.panic_buying_state_detector import summarize_microstructure_detector_from_events
from src.utils.constants import DATA_DIR


SCHEMA_VERSION = 1
REPORT_DIRNAME = "panic_buying"
TP_RULE_MARKERS = ("take_profit", "trailing", "preset_tp", "익절", "profit")
HARD_PROTECT_EMERGENCY_RULE_MARKERS = (
    "emergency",
    "protect_hard_stop",
    "scalp_hard_stop_pct",
    "scalp_preset_hard_stop_pct",
    "hard_stop",
)
FORBIDDEN_AUTOMATIONS = [
    "live_threshold_runtime_mutation",
    "take_profit_policy_change",
    "trailing_policy_change",
    "auto_sell",
    "auto_buy",
    "bot_restart",
    "provider_route_change",
]


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _report_dir() -> Path:
    return DATA_DIR / "report" / REPORT_DIRNAME


def _json_report_path(dirname: str, target_date: str) -> Path:
    return DATA_DIR / "report" / dirname / f"{dirname}_{target_date}.json"


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return default
        numeric = float(str(value).replace("%", "").replace("+", "").replace(",", "").strip())
        return numeric if math.isfinite(numeric) else default
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    numeric = _safe_float(value)
    return int(numeric) if numeric is not None else default


def _parse_dt(value: Any) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _event_fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _truthy(value: Any) -> bool:
    return _safe_str(value).lower() in {"1", "true", "yes", "y"}


def _falsey(value: Any) -> bool:
    return _safe_str(value).lower() in {"0", "false", "no", "n"}


def _is_non_real_observation(row: dict[str, Any]) -> bool:
    fields = _event_fields(row)
    stage = _safe_str(row.get("stage"))
    if _falsey(fields.get("actual_order_submitted")):
        return True
    if _truthy(fields.get("broker_order_forbidden")):
        return True
    if _truthy(fields.get("simulated_order")):
        return True
    if fields.get("simulation_book") or fields.get("simulation_owner"):
        return True
    if _truthy(fields.get("swing_intraday_probe")):
        return True
    if fields.get("probe_id") or fields.get("probe_origin_stage"):
        return True
    return "sim_" in stage or "_probe_" in stage or stage.startswith("swing_probe_")


def _exit_rule_text(row: dict[str, Any]) -> str:
    fields = _event_fields(row)
    parts = [
        row.get("stage"),
        fields.get("exit_rule"),
        fields.get("sell_reason_type"),
        fields.get("exit_decision_source"),
        fields.get("reason"),
    ]
    return " ".join(_safe_str(part).lower() for part in parts if _safe_str(part))


def _is_hard_protect_emergency_exit(row: dict[str, Any]) -> bool:
    text = _exit_rule_text(row)
    return any(marker in text for marker in HARD_PROTECT_EMERGENCY_RULE_MARKERS)


def _is_tp_like_exit(row: dict[str, Any]) -> bool:
    if _is_hard_protect_emergency_exit(row):
        return False
    text = _exit_rule_text(row)
    profit = _profit_rate(row)
    return any(marker in text for marker in TP_RULE_MARKERS) or (profit is not None and profit > 0)


def _profit_rate(row: dict[str, Any]) -> float | None:
    fields = _event_fields(row)
    return _safe_float(
        fields.get("profit_rate")
        or fields.get("realized_profit_rate")
        or fields.get("return_pct")
        or fields.get("profit_pct")
    )


def _summarize_tp_counterfactual(events: list[dict[str, Any]]) -> dict[str, Any]:
    holding_rows = [row for row in events if _safe_str(row.get("pipeline")) == "HOLDING_PIPELINE"]
    exit_rows = [row for row in holding_rows if "exit" in _safe_str(row.get("stage")) or "sell" in _safe_str(row.get("stage"))]
    real_exit_rows = [row for row in exit_rows if not _is_non_real_observation(row)]
    non_real_exit_rows = [row for row in exit_rows if _is_non_real_observation(row)]
    tp_rows = [row for row in real_exit_rows if _is_tp_like_exit(row)]
    non_real_tp_rows = [row for row in non_real_exit_rows if _is_tp_like_exit(row)]
    profits = [value for row in tp_rows for value in [_profit_rate(row)] if value is not None]
    peak_profits = [
        value
        for row in tp_rows
        for value in [_safe_float(_event_fields(row).get("peak_profit"), None)]
        if value is not None
    ]
    trailing_rows = [row for row in tp_rows if "trailing" in _exit_rule_text(row)]
    return {
        "policy": {
            "report_only": True,
            "runtime_effect": "counterfactual_only_no_order_change",
            "does_not_submit_orders": True,
        },
        "real_exit_count": len(real_exit_rows),
        "non_real_exit_count": len(non_real_exit_rows),
        "tp_like_exit_count": len(tp_rows),
        "non_real_tp_like_exit_count": len(non_real_tp_rows),
        "trailing_winner_count": len(trailing_rows),
        "avg_tp_profit_rate_pct": _avg(profits),
        "avg_tp_peak_profit_rate_pct": _avg(peak_profits),
        "candidate_context_count": len(tp_rows) + len(trailing_rows),
        "exit_rule_counts": dict(sorted(Counter(_safe_str(_event_fields(row).get("exit_rule") or "-") for row in tp_rows).items())),
    }


def _load_source_summary(target_date: str) -> dict[str, Any]:
    buy = _load_json(_json_report_path("buy_funnel_sentinel", target_date))
    hold = _load_json(_json_report_path("holding_exit_sentinel", target_date))
    panic_sell = _load_json(_json_report_path("panic_sell_defense", target_date))
    return {
        "buy_funnel_sentinel": {
            "path": str(_json_report_path("buy_funnel_sentinel", target_date)),
            "exists": _json_report_path("buy_funnel_sentinel", target_date).exists(),
            "primary": ((buy or {}).get("classification") or {}).get("primary") if isinstance(buy, dict) else None,
        },
        "holding_exit_sentinel": {
            "path": str(_json_report_path("holding_exit_sentinel", target_date)),
            "exists": _json_report_path("holding_exit_sentinel", target_date).exists(),
            "primary": ((hold or {}).get("classification") or {}).get("primary") if isinstance(hold, dict) else None,
        },
        "panic_sell_defense": {
            "path": str(_json_report_path("panic_sell_defense", target_date)),
            "exists": _json_report_path("panic_sell_defense", target_date).exists(),
            "panic_state": (panic_sell or {}).get("panic_state") if isinstance(panic_sell, dict) else None,
        },
    }


def _resolve_panic_buy_state(micro: dict[str, Any]) -> tuple[str, list[str]]:
    exhausted = _safe_int(micro.get("exhaustion_confirmed_count"), 0)
    exhaustion_watch = _safe_int(micro.get("exhaustion_candidate_count"), 0)
    active = _safe_int(micro.get("panic_buy_active_count"), 0)
    watch = _safe_int(micro.get("panic_buy_watch_count"), 0)
    if exhausted > 0:
        return "BUYING_EXHAUSTED", [f"exhaustion_confirmed_count={exhausted}"]
    if exhaustion_watch > 0:
        return "EXHAUSTION_WATCH", [f"exhaustion_candidate_count={exhaustion_watch}"]
    if active > 0:
        return "PANIC_BUY", [f"panic_buy_active_count={active}"]
    if watch > 0:
        return "PANIC_BUY_WATCH", [f"panic_buy_watch_count={watch}"]
    return "NORMAL", ["no panic buying threshold breached"]


def _panic_buy_metrics(micro: dict[str, Any]) -> dict[str, Any]:
    metrics = micro.get("metrics") if isinstance(micro.get("metrics"), dict) else {}
    return {
        "evaluated_symbol_count": _safe_int(micro.get("evaluated_symbol_count"), 0),
        "panic_buy_signal_count": _safe_int(micro.get("panic_buy_signal_count"), 0),
        "panic_buy_active_count": _safe_int(micro.get("panic_buy_active_count"), 0),
        "panic_buy_watch_count": _safe_int(micro.get("panic_buy_watch_count"), 0),
        "allow_tp_override_count": _safe_int(micro.get("allow_tp_override_count"), 0),
        "allow_runner_count": _safe_int(micro.get("allow_runner_count"), 0),
        "missing_orderbook_count": _safe_int(micro.get("missing_orderbook_count"), 0),
        "degraded_orderbook_count": _safe_int(micro.get("degraded_orderbook_count"), 0),
        "missing_trade_aggressor_count": _safe_int(micro.get("missing_trade_aggressor_count"), 0),
        "max_panic_buy_score": _safe_float(metrics.get("max_panic_buy_score"), 0.0),
        "avg_confidence": _safe_float(metrics.get("avg_confidence"), 0.0),
    }


def _exhaustion_metrics(micro: dict[str, Any]) -> dict[str, Any]:
    metrics = micro.get("metrics") if isinstance(micro.get("metrics"), dict) else {}
    return {
        "exhaustion_candidate_count": _safe_int(micro.get("exhaustion_candidate_count"), 0),
        "exhaustion_confirmed_count": _safe_int(micro.get("exhaustion_confirmed_count"), 0),
        "force_exit_runner_count": _safe_int(micro.get("force_exit_runner_count"), 0),
        "max_exhaustion_score": _safe_float(metrics.get("max_exhaustion_score"), 0.0),
    }


def _canary_candidates(
    panic_buy_state: str,
    panic_metrics: dict[str, Any],
    exhaustion_metrics: dict[str, Any],
    tp_counterfactual: dict[str, Any],
) -> list[dict[str, Any]]:
    active = _safe_int(panic_metrics.get("panic_buy_active_count"), 0)
    tp_context = _safe_int(tp_counterfactual.get("candidate_context_count"), 0)
    avg_confidence = _safe_float(panic_metrics.get("avg_confidence"), 0.0) or 0.0
    candidate_ready = panic_buy_state == "PANIC_BUY" and active > 0 and tp_context > 0 and avg_confidence >= 0.55
    status = "report_only_candidate" if candidate_ready else "hold_until_confirmed_panic_buy_with_tp_context"
    if avg_confidence < 0.55 and active > 0:
        status = "hold_low_detector_confidence"
    return [
        {
            "family": "panic_buy_runner_tp_canary",
            "status": status,
            "allowed_runtime_apply": False,
            "next_owner": "future_checklist_approval_required",
            "guard": (
                "report-only V1; future canary must keep hard/protect/emergency stop priority, "
                "receipt/provenance safety, same-stage owner guard, and opportunity-vs-giveback rollback"
            ),
            "source_metrics": {
                "panic_buy_state": panic_buy_state,
                "panic_buy_active_count": active,
                "exhaustion_confirmed_count": _safe_int(exhaustion_metrics.get("exhaustion_confirmed_count"), 0),
                "tp_counterfactual_count": tp_context,
                "avg_confidence": avg_confidence,
            },
        }
    ]


def build_panic_buying_report(
    target_date: str,
    *,
    as_of: datetime | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    events = _load_jsonl(_pipeline_events_path(target_date))
    event_datetimes = [dt for row in events for dt in [_parse_dt(row.get("emitted_at"))] if dt is not None]
    latest_dt = max(event_datetimes) if event_datetimes else None
    if as_of is None:
        as_of = datetime.now()
    micro = summarize_microstructure_detector_from_events(events, as_of=as_of)
    panic_buy_state, reasons = _resolve_panic_buy_state(micro)
    panic_metrics = _panic_buy_metrics(micro)
    exhaustion = _exhaustion_metrics(micro)
    tp_counterfactual = _summarize_tp_counterfactual(events)
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "panic_buying",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(timespec="seconds"),
        "latest_event_at": latest_dt.isoformat(timespec="seconds") if latest_dt else None,
        "dry_run": bool(dry_run),
        "policy": {
            "report_only": True,
            "runtime_effect": "report_only_no_mutation",
            "live_runtime_effect": False,
            "forbidden_automations": FORBIDDEN_AUTOMATIONS,
        },
        "panic_buy_state": panic_buy_state,
        "panic_buy_state_reasons": reasons,
        "panic_buy_metrics": panic_metrics,
        "exhaustion_metrics": exhaustion,
        "microstructure_detector": micro,
        "tp_counterfactual_summary": tp_counterfactual,
        "canary_candidates": _canary_candidates(panic_buy_state, panic_metrics, exhaustion, tp_counterfactual),
        "source_summary": _load_source_summary(target_date),
        "qna_policy": {
            "should_change_take_profit_now": "no; report-only until separate approval artifact and rollback guard exist",
            "panic_buy_is_new_buy_signal": "no; it is runner/TP attribution context for existing long positions",
            "exhaustion_behavior": "future runner cleanup or tight trailing candidate only, no V1 runtime action",
            "performance_read": "closed PnL, TP counterfactual, and detector confidence must be read separately",
        },
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def build_markdown(report: dict[str, Any]) -> str:
    panic = report["panic_buy_metrics"]
    exhaustion = report["exhaustion_metrics"]
    tp = report["tp_counterfactual_summary"]
    micro = report.get("microstructure_detector") if isinstance(report.get("microstructure_detector"), dict) else {}
    lines = [
        f"# Panic Buying {report['target_date']}",
        "",
        "## 판정",
        "",
        f"- panic_buy_state: `{report['panic_buy_state']}`",
        f"- report_only: `{str(report['policy']['report_only']).lower()}`",
        f"- runtime_effect: `{report['policy']['runtime_effect']}`",
        f"- as_of: `{report['as_of']}`",
        f"- latest_event_at: `{report.get('latest_event_at') or '-'}`",
        f"- reasons: `{'; '.join(report.get('panic_buy_state_reasons') or [])}`",
        "",
        "## 패닉바잉 지표",
        "",
        f"- evaluated_symbol_count: `{panic['evaluated_symbol_count']}`",
        f"- panic_buy_active_count: `{panic['panic_buy_active_count']}`",
        f"- panic_buy_watch_count: `{panic['panic_buy_watch_count']}`",
        f"- allow_tp_override_count: `{panic['allow_tp_override_count']}`",
        f"- allow_runner_count: `{panic['allow_runner_count']}`",
        f"- max_panic_buy_score: `{_fmt(panic['max_panic_buy_score'])}`",
        f"- avg_confidence: `{_fmt(panic['avg_confidence'])}`",
        "",
        "## 소진 지표",
        "",
        f"- exhaustion_candidate_count: `{exhaustion['exhaustion_candidate_count']}`",
        f"- exhaustion_confirmed_count: `{exhaustion['exhaustion_confirmed_count']}`",
        f"- force_exit_runner_count: `{exhaustion['force_exit_runner_count']}`",
        f"- max_exhaustion_score: `{_fmt(exhaustion['max_exhaustion_score'])}`",
        "",
        "## TP Counterfactual",
        "",
        f"- tp_like_exit_count: `{tp['tp_like_exit_count']}`",
        f"- trailing_winner_count: `{tp['trailing_winner_count']}`",
        f"- candidate_context_count: `{tp['candidate_context_count']}`",
        f"- avg_tp_profit_rate_pct: `{_fmt(tp['avg_tp_profit_rate_pct'])}`",
        f"- runtime_effect: `{tp['policy']['runtime_effect']}`",
        "",
        "## Microstructure Detector",
        "",
        f"- missing_orderbook_count: `{micro.get('missing_orderbook_count', 0)}`",
        f"- degraded_orderbook_count: `{micro.get('degraded_orderbook_count', 0)}`",
        f"- missing_trade_aggressor_count: `{micro.get('missing_trade_aggressor_count', 0)}`",
        "",
        "## Canary Candidates",
        "",
    ]
    lines.extend(
        f"- `{item['family']}`: `{item['status']}`, allowed_runtime_apply=`{str(item['allowed_runtime_apply']).lower()}`"
        for item in report["canary_candidates"]
    )
    lines.extend(["", "## 금지된 자동변경", ""])
    lines.extend(f"- `{item}`" for item in report["policy"]["forbidden_automations"])
    lines.append("")
    return "\n".join(lines)


def save_report_artifacts(report: dict[str, Any]) -> dict[str, str]:
    report_dir = _report_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    target_date = report["target_date"]
    json_path = report_dir / f"panic_buying_{target_date}.json"
    md_path = report_dir / f"panic_buying_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def _parse_as_of(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = _parse_dt(value)
    if parsed is None:
        raise ValueError(f"invalid --as-of value: {value}")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build report-only panic buying report.")
    parser.add_argument("--date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--as-of", dest="as_of", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_panic_buying_report(
        args.target_date,
        as_of=_parse_as_of(args.as_of) if args.as_of else None,
        dry_run=args.dry_run,
    )
    artifacts = {} if args.dry_run else save_report_artifacts(report)
    summary = {
        "status": "success",
        "target_date": args.target_date,
        "panic_buy_state": report["panic_buy_state"],
        "runtime_effect": report["policy"]["runtime_effect"],
        "artifacts": artifacts,
    }
    if args.print_json:
        print(json.dumps(report if args.dry_run else summary, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
