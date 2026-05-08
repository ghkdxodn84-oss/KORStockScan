"""Build the daily EV performance report for unattended threshold calibration."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.build_code_improvement_workorder import code_improvement_workorder_paths
from src.engine.scalping_pattern_lab_automation import automation_report_paths
from src.engine.threshold_cycle_preopen_apply import apply_manifest_path


MONITOR_SNAPSHOT_DIR = REPORT_DIR / "monitor_snapshots"
CALIBRATION_REPORT_DIR = REPORT_DIR / "threshold_cycle_calibration"
EV_REPORT_DIR = REPORT_DIR / "threshold_cycle_ev"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def ev_report_paths(target_date: str) -> tuple[Path, Path]:
    base = EV_REPORT_DIR / f"threshold_cycle_ev_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _calibration_path(target_date: str) -> Path:
    postclose = CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_postclose.json"
    if postclose.exists():
        return postclose
    return CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_intraday.json"


def _selected_families(apply_manifest: dict[str, Any]) -> list[str]:
    selected = apply_manifest.get("auto_apply_selected")
    if isinstance(selected, list) and selected:
        return [str(item.get("family") or "") for item in selected if isinstance(item, dict) and item.get("family")]
    env_manifest = apply_manifest.get("runtime_env_overrides")
    if isinstance(env_manifest, dict) and env_manifest:
        return ["runtime_env_override"]
    return []


def _cohort_decisions(calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = calibration_report.get("post_apply_attribution")
    attribution = attribution if isinstance(attribution, dict) else {}
    candidates = calibration_report.get("calibration_candidates")
    candidate_by_family = {
        str(item.get("family") or ""): item for item in candidates if isinstance(item, dict) and item.get("family")
    } if isinstance(candidates, list) else {}
    decisions = attribution.get("calibration_decisions")
    if isinstance(decisions, list):
        merged: list[dict[str, Any]] = []
        for item in decisions:
            if not isinstance(item, dict):
                continue
            family = str(item.get("family") or "")
            source = candidate_by_family.get(family) or {}
            merged.append(
                {
                    **item,
                    "sample_count": item.get("sample_count", source.get("sample_count")),
                    "sample_floor": item.get("sample_floor", source.get("sample_floor")),
                }
            )
        return merged
    if not isinstance(candidates, list):
        return []
    return [
        {
            "family": item.get("family"),
            "calibration_state": item.get("calibration_state"),
            "calibration_reason": item.get("calibration_reason"),
            "sample_count": item.get("sample_count"),
            "sample_floor": item.get("sample_floor"),
        }
        for item in candidates
        if isinstance(item, dict)
    ]


def _pattern_lab_automation_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = automation_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "gemini_fresh": False,
                "claude_fresh": False,
                "consensus_count": 0,
                "auto_family_candidate_count": 0,
                "code_improvement_order_count": 0,
                "top_consensus_findings": [],
                "top_code_improvement_orders": [],
            },
            None,
            ["pattern_lab_automation_missing"],
        )
    summary = payload.get("ev_report_summary") if isinstance(payload.get("ev_report_summary"), dict) else {}
    warnings: list[str] = []
    if not bool(summary.get("gemini_fresh")):
        warnings.append("pattern_lab_gemini_stale")
    if not bool(summary.get("claude_fresh")):
        warnings.append("pattern_lab_claude_stale")
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "gemini_fresh": bool(summary.get("gemini_fresh")),
            "claude_fresh": bool(summary.get("claude_fresh")),
            "consensus_count": _safe_int(summary.get("consensus_count"), 0),
            "auto_family_candidate_count": _safe_int(summary.get("auto_family_candidate_count"), 0),
            "code_improvement_order_count": _safe_int(summary.get("code_improvement_order_count"), 0),
            "top_consensus_findings": list(summary.get("top_consensus_findings") or [])[:3],
            "top_code_improvement_orders": list(summary.get("top_code_improvement_orders") or [])[:3],
        },
        str(json_path),
        warnings,
    )


def _code_improvement_workorder_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, md_path = code_improvement_workorder_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "markdown": str(md_path) if md_path.exists() else None,
                "selected_order_count": 0,
                "decision_counts": {},
                "top_orders": [],
            },
            None,
            ["code_improvement_workorder_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    orders = payload.get("orders") if isinstance(payload.get("orders"), list) else []
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "markdown": str(md_path) if md_path.exists() else None,
            "selected_order_count": _safe_int(summary.get("selected_order_count"), 0),
            "decision_counts": summary.get("decision_counts") if isinstance(summary.get("decision_counts"), dict) else {},
            "top_orders": [
                {
                    "order_id": item.get("order_id"),
                    "decision": item.get("decision"),
                    "target_subsystem": item.get("target_subsystem"),
                }
                for item in orders[:3]
                if isinstance(item, dict)
            ],
        },
        str(json_path),
        [],
    )


def build_threshold_cycle_ev_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    trade_review_path = MONITOR_SNAPSHOT_DIR / f"trade_review_{target_date}.json"
    performance_path = MONITOR_SNAPSHOT_DIR / f"performance_tuning_{target_date}.json"
    calibration_path = _calibration_path(target_date)
    apply_path = apply_manifest_path(target_date)

    trade_review = _load_json(trade_review_path)
    performance = _load_json(performance_path)
    calibration = _load_json(calibration_path)
    apply_manifest = _load_json(apply_path)
    trade_metrics = trade_review.get("metrics") if isinstance(trade_review.get("metrics"), dict) else {}
    perf_metrics = performance.get("metrics") if isinstance(performance.get("metrics"), dict) else {}
    pattern_lab_summary, pattern_lab_path, pattern_lab_warnings = _pattern_lab_automation_summary(target_date)
    code_workorder_summary, code_workorder_path, code_workorder_warnings = _code_improvement_workorder_summary(target_date)
    selected_families = _selected_families(apply_manifest)
    completed = _safe_int(trade_metrics.get("completed_trades"), 0)
    win = _safe_int(trade_metrics.get("win_trades"), 0)
    loss = _safe_int(trade_metrics.get("loss_trades"), 0)
    win_rate = round((win / completed) * 100.0, 2) if completed else 0.0
    budget_pass = _safe_int(perf_metrics.get("budget_pass_events"), 0)
    submitted = _safe_int(perf_metrics.get("order_bundle_submitted_events"), 0)
    submitted_rate = round((submitted / budget_pass) * 100.0, 2) if budget_pass else 0.0
    full_fill_completed_avg = _safe_float(perf_metrics.get("full_fill_completed_avg_profit_rate"), 0.0)

    report = {
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "purpose": "daily_ev_performance_report_for_unattended_threshold_calibration",
        "runtime_apply": {
            "apply_manifest": str(apply_path) if apply_path.exists() else None,
            "runtime_change": bool(apply_manifest.get("runtime_change")),
            "status": apply_manifest.get("status"),
            "selected_families": selected_families,
            "runtime_env_file": apply_manifest.get("runtime_env_file"),
        },
        "daily_ev_summary": {
            "completed_trades": completed,
            "open_trades": _safe_int(trade_metrics.get("open_trades"), 0),
            "win_trades": win,
            "loss_trades": loss,
            "win_rate_pct": win_rate,
            "avg_profit_rate_pct": round(_safe_float(trade_metrics.get("avg_profit_rate"), 0.0), 4),
            "realized_pnl_krw": _safe_int(trade_metrics.get("realized_pnl_krw"), 0),
            "full_fill_completed_avg_profit_rate_pct": round(full_fill_completed_avg, 4),
        },
        "entry_funnel": {
            "budget_pass_events": budget_pass,
            "order_bundle_submitted_events": submitted,
            "budget_pass_to_submitted_rate_pct": submitted_rate,
            "latency_block_events": _safe_int(perf_metrics.get("latency_block_events"), 0),
            "latency_pass_events": _safe_int(perf_metrics.get("latency_pass_events"), 0),
            "full_fill_events": _safe_int(perf_metrics.get("full_fill_events"), 0),
            "partial_fill_events": _safe_int(perf_metrics.get("partial_fill_events"), 0),
        },
        "holding_exit": {
            "holding_reviews": _safe_int(perf_metrics.get("holding_reviews"), 0),
            "exit_signals": _safe_int(perf_metrics.get("exit_signals"), 0),
            "holding_review_ms_p95": round(_safe_float(perf_metrics.get("holding_review_ms_p95"), 0.0), 2),
            "holding_ai_cache_hit_ratio": round(_safe_float(perf_metrics.get("holding_ai_cache_hit_ratio"), 0.0), 4),
        },
        "calibration_outcome": {
            "calibration_report": str(calibration_path) if calibration_path.exists() else None,
            "run_phase": calibration.get("run_phase"),
            "runtime_change": bool(calibration.get("runtime_change")),
            "decisions": _cohort_decisions(calibration),
        },
        "pattern_lab_automation": pattern_lab_summary,
        "code_improvement_workorder": code_workorder_summary,
        "sources": {
            "trade_review": str(trade_review_path) if trade_review_path.exists() else None,
            "performance_tuning": str(performance_path) if performance_path.exists() else None,
            "calibration": str(calibration_path) if calibration_path.exists() else None,
            "apply_manifest": str(apply_path) if apply_path.exists() else None,
            "pattern_lab_automation": pattern_lab_path,
            "code_improvement_workorder": code_workorder_path,
        },
        "warnings": [
            message
            for message in [
                "trade_review_missing" if not trade_review_path.exists() else "",
                "performance_tuning_missing" if not performance_path.exists() else "",
                "calibration_report_missing" if not calibration_path.exists() else "",
                "apply_manifest_missing" if not apply_path.exists() else "",
                *pattern_lab_warnings,
                *code_workorder_warnings,
            ]
            if message
        ],
    }
    EV_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = ev_report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_threshold_cycle_ev_markdown(report), encoding="utf-8")
    return report


def render_threshold_cycle_ev_markdown(report: dict[str, Any]) -> str:
    ev = report.get("daily_ev_summary") if isinstance(report.get("daily_ev_summary"), dict) else {}
    funnel = report.get("entry_funnel") if isinstance(report.get("entry_funnel"), dict) else {}
    holding = report.get("holding_exit") if isinstance(report.get("holding_exit"), dict) else {}
    runtime = report.get("runtime_apply") if isinstance(report.get("runtime_apply"), dict) else {}
    pattern_lab = report.get("pattern_lab_automation") if isinstance(report.get("pattern_lab_automation"), dict) else {}
    code_workorder = report.get("code_improvement_workorder") if isinstance(report.get("code_improvement_workorder"), dict) else {}
    decisions = ((report.get("calibration_outcome") or {}).get("decisions") or []) if isinstance(report.get("calibration_outcome"), dict) else []
    lines = [
        f"# Threshold Cycle Daily EV Report - {report.get('date')}",
        "",
        "## Runtime Apply",
        f"- status: `{runtime.get('status')}`",
        f"- runtime_change: `{runtime.get('runtime_change')}`",
        f"- selected_families: `{', '.join(runtime.get('selected_families') or []) or '-'}`",
        "",
        "## Daily EV",
        f"- completed: `{ev.get('completed_trades')}` / open: `{ev.get('open_trades')}`",
        f"- win/loss: `{ev.get('win_trades')}` / `{ev.get('loss_trades')}` (`{ev.get('win_rate_pct')}`%)",
        f"- avg_profit_rate: `{ev.get('avg_profit_rate_pct')}`%",
        f"- realized_pnl_krw: `{ev.get('realized_pnl_krw')}`",
        f"- full_fill_completed_avg_profit_rate: `{ev.get('full_fill_completed_avg_profit_rate_pct')}`%",
        "",
        "## Entry Funnel",
        f"- budget_pass_to_submitted: `{funnel.get('order_bundle_submitted_events')}` / `{funnel.get('budget_pass_events')}` (`{funnel.get('budget_pass_to_submitted_rate_pct')}`%)",
        f"- latency pass/block: `{funnel.get('latency_pass_events')}` / `{funnel.get('latency_block_events')}`",
        f"- full/partial fill: `{funnel.get('full_fill_events')}` / `{funnel.get('partial_fill_events')}`",
        "",
        "## Holding Exit",
        f"- holding_reviews: `{holding.get('holding_reviews')}`",
        f"- exit_signals: `{holding.get('exit_signals')}`",
        f"- holding_review_ms_p95: `{holding.get('holding_review_ms_p95')}`",
        "",
        "## Pattern Lab Automation",
        f"- artifact: `{pattern_lab.get('artifact') or '-'}`",
        f"- fresh: gemini=`{pattern_lab.get('gemini_fresh')}` claude=`{pattern_lab.get('claude_fresh')}`",
        f"- consensus/orders/family_candidates: `{pattern_lab.get('consensus_count')}` / `{pattern_lab.get('code_improvement_order_count')}` / `{pattern_lab.get('auto_family_candidate_count')}`",
        "",
        "## Code Improvement Workorder",
        f"- artifact: `{code_workorder.get('artifact') or '-'}`",
        f"- markdown: `{code_workorder.get('markdown') or '-'}`",
        f"- selected_order_count: `{code_workorder.get('selected_order_count')}`",
        f"- decision_counts: `{code_workorder.get('decision_counts')}`",
        "",
        "## Calibration Decisions",
    ]
    top_orders = code_workorder.get("top_orders") if isinstance(code_workorder.get("top_orders"), list) else []
    if top_orders:
        lines.extend(["## Code Improvement Top Orders"])
        for item in top_orders[:3]:
            if isinstance(item, dict):
                lines.append(
                    f"- `{item.get('order_id')}` decision=`{item.get('decision')}` subsystem=`{item.get('target_subsystem')}`"
                )
        lines.append("")
    top_findings = pattern_lab.get("top_consensus_findings") if isinstance(pattern_lab.get("top_consensus_findings"), list) else []
    if top_findings:
        lines.extend(["## Pattern Lab Top Findings"])
        for item in top_findings[:3]:
            if isinstance(item, dict):
                lines.append(
                    f"- `{item.get('title')}` route=`{item.get('route')}` family=`{item.get('mapped_family') or '-'}`"
                )
        lines.append("")
    if decisions:
        for item in decisions:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('family')}`: `{item.get('calibration_state')}` "
                f"sample=`{item.get('sample_count')}/{item.get('sample_floor')}`"
            )
    else:
        lines.append("- no calibration decisions")
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend([f"- `{warning}`" for warning in warnings])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build threshold-cycle daily EV performance report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_threshold_cycle_ev_report(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
