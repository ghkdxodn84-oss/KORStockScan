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
from src.engine.swing_pattern_lab_automation import swing_pattern_lab_automation_report_paths
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


def _wait6579_counterfactual_summary(target_date: str) -> tuple[dict[str, Any], str | None]:
    path = MONITOR_SNAPSHOT_DIR / f"wait6579_ev_cohort_{target_date}.json"
    payload = _load_json(path)
    summary = payload.get("counterfactual_summary") if isinstance(payload.get("counterfactual_summary"), dict) else {}
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    approval = payload.get("approval_gate") if isinstance(payload.get("approval_gate"), dict) else {}
    if not payload:
        return {}, None
    if not summary:
        summary = {
            "book": "scalp_score65_74_probe_counterfactual",
            "role": "missed_buy_probe_counterfactual",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": "counterfactual_report_only",
            "calibration_authority": "missed_probe_ev_only_not_broker_execution",
            "total_candidates": _safe_int(metrics.get("total_candidates"), 0),
            "score65_74_probe_candidates": _safe_int(metrics.get("score65_74_probe_candidates"), 0),
            "avg_expected_ev_pct": round(_safe_float(metrics.get("avg_expected_ev_pct"), 0.0), 4),
            "expected_ev_krw_sum": _safe_int(metrics.get("expected_ev_krw_sum"), 0),
            "source_authority": "observe_only_threshold_relaxation_input",
            "real_execution_quality_source": "none",
        }
    summary = dict(summary)
    summary["approval_gate"] = {
        "min_sample_gate_passed": bool(approval.get("min_sample_gate_passed")),
        "threshold_relaxation_approved": bool(approval.get("threshold_relaxation_approved")),
        "full_samples": _safe_int(approval.get("full_samples"), 0),
        "partial_samples": _safe_int(approval.get("partial_samples"), 0),
    }
    return summary, str(path)


def _selected_families(apply_manifest: dict[str, Any]) -> list[str]:
    selected = apply_manifest.get("auto_apply_selected")
    if isinstance(selected, list) and selected:
        families = [str(item.get("family") or "") for item in selected if isinstance(item, dict) and item.get("family")]
        swing_selected = ((apply_manifest.get("swing_runtime_approval") or {}).get("selected") or [])
        families.extend(
            str(item.get("family") or "") for item in swing_selected if isinstance(item, dict) and item.get("family")
        )
        return families
    swing_selected = ((apply_manifest.get("swing_runtime_approval") or {}).get("selected") or [])
    if isinstance(swing_selected, list) and swing_selected:
        return [str(item.get("family") or "") for item in swing_selected if isinstance(item, dict) and item.get("family")]
    env_manifest = apply_manifest.get("runtime_env_overrides")
    if isinstance(env_manifest, dict) and env_manifest:
        return ["runtime_env_override"]
    return []


def _swing_runtime_approval_summary(apply_manifest: dict[str, Any]) -> dict[str, Any]:
    swing = apply_manifest.get("swing_runtime_approval") if isinstance(apply_manifest.get("swing_runtime_approval"), dict) else {}
    requests = swing.get("requests") if isinstance(swing.get("requests"), list) else []
    approved = swing.get("approved_requests") if isinstance(swing.get("approved_requests"), list) else []
    selected = swing.get("selected") if isinstance(swing.get("selected"), list) else []
    decisions = swing.get("decisions") if isinstance(swing.get("decisions"), list) else []
    real_canary_policy = (
        swing.get("real_canary_policy") if isinstance(swing.get("real_canary_policy"), dict) else {}
    )
    scale_in_real_canary_policy = (
        swing.get("scale_in_real_canary_policy")
        if isinstance(swing.get("scale_in_real_canary_policy"), dict)
        else {}
    )
    scale_in_selected = [
        item
        for item in selected
        if isinstance(item, dict)
        and str(item.get("policy_id") or item.get("family") or "") == "swing_scale_in_real_canary_phase0"
    ]
    return {
        "request_report": swing.get("request_report"),
        "approval_artifact": swing.get("approval_artifact"),
        "scale_in_real_canary_approval_artifact": swing.get("scale_in_real_canary_approval_artifact"),
        "requested": _safe_int(swing.get("requested"), len(requests)),
        "approved": _safe_int(swing.get("approved"), len(approved)),
        "selected_live_dry_run": len(selected),
        "selected_scale_in_real_canary": len(scale_in_selected),
        "dry_run_forced": bool(swing.get("dry_run_forced")),
        "real_canary_policy": real_canary_policy,
        "scale_in_real_canary_policy": scale_in_real_canary_policy,
        "real_execution_quality": {
            "scale_in_canary_selected": len(scale_in_selected),
            "execution_quality_source": "real_only",
            "sim_probe_ev_source": "separate_from_broker_execution_quality",
        },
        "blocked": list(swing.get("blocked") or []),
        "requests": [
            {
                "approval_id": item.get("approval_id"),
                "family": item.get("family"),
                "stage": item.get("stage"),
                "tradeoff_score": item.get("tradeoff_score"),
                "target_env_keys": item.get("target_env_keys"),
                "recommended_values": item.get("recommended_values"),
            }
            for item in requests
            if isinstance(item, dict)
        ],
        "decisions": decisions,
    }


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


def _approval_requests(calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = calibration_report.get("calibration_candidates")
    if not isinstance(candidates, list):
        return []
    requests: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        if not bool(item.get("human_approval_required")):
            continue
        if str(item.get("calibration_state") or "") != "approval_required":
            continue
        requests.append(
            {
                "family": item.get("family"),
                "stage": item.get("stage"),
                "calibration_reason": item.get("calibration_reason"),
                "current_values": item.get("current_values"),
                "recommended_values": item.get("recommended_values"),
                "sample_count": item.get("sample_count"),
                "sample_floor": item.get("sample_floor"),
            }
        )
    return requests


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


def _swing_pattern_lab_automation_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = swing_pattern_lab_automation_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "findings_count": 0,
                "code_improvement_order_count": 0,
                "data_quality_warning_count": 0,
                "carryover_warning_count": 0,
                "population_split_available": False,
                "top_findings": [],
                "top_orders": [],
            },
            None,
            ["swing_pattern_lab_automation_missing"],
        )
    summary = payload.get("ev_report_summary") if isinstance(payload.get("ev_report_summary"), dict) else {}
    warnings: list[str] = []
    dq_warnings = (payload.get("data_quality") or {}).get("warnings", [])
    if dq_warnings:
        warnings.extend(f"swing_lab_dq:{w}" for w in (dq_warnings if isinstance(dq_warnings, list) else []))
    if summary.get("stale_reason"):
        warnings.append(f"swing_lab_stale:{summary['stale_reason']}")
    carryover_count = _safe_int(summary.get("carryover_warning_count"), 0)
    if carryover_count > 0:
        warnings.append(f"swing_lab_carryover:{carryover_count}")
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "deepseek_lab_available": bool(summary.get("deepseek_lab_available")),
            "findings_count": _safe_int(summary.get("findings_count"), 0),
            "code_improvement_order_count": _safe_int(summary.get("code_improvement_order_count"), 0),
            "data_quality_warning_count": _safe_int(summary.get("data_quality_warning_count"), 0),
            "carryover_warning_count": carryover_count,
            "population_split_available": bool(summary.get("population_split_available")),
            "top_findings": [
                {
                    "finding_id": item.get("finding_id"),
                    "title": item.get("title"),
                    "route": item.get("route"),
                }
                for item in (payload.get("consensus_findings") or [])[:3]
                if isinstance(item, dict)
            ],
            "top_orders": [
                {
                    "order_id": item.get("order_id"),
                    "title": item.get("title"),
                    "decision": item.get("decision"),
                }
                for item in (payload.get("code_improvement_orders") or [])[:3]
                if isinstance(item, dict)
            ],
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
    scalp_simulator = calibration.get("scalp_simulator") if isinstance(calibration.get("scalp_simulator"), dict) else {}
    wait6579_counterfactual, wait6579_counterfactual_path = _wait6579_counterfactual_summary(target_date)
    completed_by_source = (
        calibration.get("completed_by_source")
        if isinstance(calibration.get("completed_by_source"), dict)
        else {}
    )
    pattern_lab_summary, pattern_lab_path, pattern_lab_warnings = _pattern_lab_automation_summary(target_date)
    swing_lab_summary, swing_lab_path, swing_lab_warnings = _swing_pattern_lab_automation_summary(target_date)
    code_workorder_summary, code_workorder_path, code_workorder_warnings = _code_improvement_workorder_summary(target_date)
    selected_families = _selected_families(apply_manifest)
    swing_runtime_approval = _swing_runtime_approval_summary(apply_manifest)
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
            "source_split": completed_by_source,
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
        "scalp_simulator": scalp_simulator,
        "missed_probe_counterfactual": wait6579_counterfactual,
        "calibration_outcome": {
            "calibration_report": str(calibration_path) if calibration_path.exists() else None,
            "run_phase": calibration.get("run_phase"),
            "runtime_change": bool(calibration.get("runtime_change")),
            "decisions": _cohort_decisions(calibration),
        },
        "approval_requests": _approval_requests(calibration),
        "swing_runtime_approval": swing_runtime_approval,
        "pattern_lab_automation": pattern_lab_summary,
        "swing_pattern_lab_automation": swing_lab_summary,
        "code_improvement_workorder": code_workorder_summary,
        "sources": {
            "trade_review": str(trade_review_path) if trade_review_path.exists() else None,
            "performance_tuning": str(performance_path) if performance_path.exists() else None,
            "calibration": str(calibration_path) if calibration_path.exists() else None,
            "apply_manifest": str(apply_path) if apply_path.exists() else None,
            "pattern_lab_automation": pattern_lab_path,
            "swing_pattern_lab_automation": swing_lab_path,
            "code_improvement_workorder": code_workorder_path,
            "missed_probe_counterfactual": wait6579_counterfactual_path,
        },
        "warnings": [
            message
            for message in [
                "trade_review_missing" if not trade_review_path.exists() else "",
                "performance_tuning_missing" if not performance_path.exists() else "",
                "calibration_report_missing" if not calibration_path.exists() else "",
                "apply_manifest_missing" if not apply_path.exists() else "",
                *pattern_lab_warnings,
                *swing_lab_warnings,
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
    scalp_sim = report.get("scalp_simulator") if isinstance(report.get("scalp_simulator"), dict) else {}
    missed_probe = report.get("missed_probe_counterfactual") if isinstance(report.get("missed_probe_counterfactual"), dict) else {}
    runtime = report.get("runtime_apply") if isinstance(report.get("runtime_apply"), dict) else {}
    pattern_lab = report.get("pattern_lab_automation") if isinstance(report.get("pattern_lab_automation"), dict) else {}
    swing_lab = report.get("swing_pattern_lab_automation") if isinstance(report.get("swing_pattern_lab_automation"), dict) else {}
    swing_runtime = report.get("swing_runtime_approval") if isinstance(report.get("swing_runtime_approval"), dict) else {}
    code_workorder = report.get("code_improvement_workorder") if isinstance(report.get("code_improvement_workorder"), dict) else {}
    approval_requests = report.get("approval_requests") if isinstance(report.get("approval_requests"), list) else []
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
        "## Scalp Simulator",
        f"- authority: `{scalp_sim.get('calibration_authority') or '-'}` / fill_policy: `{scalp_sim.get('fill_policy') or '-'}`",
        f"- armed/filled/sold: `{scalp_sim.get('entry_armed')}` / `{scalp_sim.get('buy_filled')}` / `{scalp_sim.get('sell_completed')}`",
        f"- expired/unpriced/duplicate: `{scalp_sim.get('entry_expired')}` / `{scalp_sim.get('entry_unpriced')}` / `{scalp_sim.get('duplicate_buy_signal')}`",
        f"- completed_profit_summary: `{scalp_sim.get('completed_profit_summary') or {}}`",
        "",
        "## Missed Probe Counterfactual",
        f"- book: `{missed_probe.get('book') or '-'}` / role: `{missed_probe.get('role') or '-'}`",
        f"- total/score65_74: `{missed_probe.get('total_candidates')}` / `{missed_probe.get('score65_74_probe_candidates')}`",
        f"- avg_expected_ev: `{missed_probe.get('avg_expected_ev_pct')}`% / score65_74_avg_expected_ev: `{missed_probe.get('score65_74_avg_expected_ev_pct')}`%",
        f"- actual_order_submitted: `{missed_probe.get('actual_order_submitted')}` / broker_order_forbidden: `{missed_probe.get('broker_order_forbidden')}`",
        f"- authority: `{missed_probe.get('calibration_authority') or '-'}`",
        "",
        "## Pattern Lab Automation",
        f"- artifact: `{pattern_lab.get('artifact') or '-'}`",
        f"- fresh: gemini=`{pattern_lab.get('gemini_fresh')}` claude=`{pattern_lab.get('claude_fresh')}`",
        f"- consensus/orders/family_candidates: `{pattern_lab.get('consensus_count')}` / `{pattern_lab.get('code_improvement_order_count')}` / `{pattern_lab.get('auto_family_candidate_count')}`",
        "",
        "## Swing Pattern Lab Automation",
        f"- artifact: `{swing_lab.get('artifact') or '-'}`",
        f"- deepseek_lab_available: `{swing_lab.get('deepseek_lab_available')}`",
        f"- findings/orders: `{swing_lab.get('findings_count')}` / `{swing_lab.get('code_improvement_order_count')}`",
        f"- data_quality_warnings: `{swing_lab.get('data_quality_warning_count')}`",
        f"- carryover_warnings: `{swing_lab.get('carryover_warning_count')}`",
        f"- population_split_available: `{swing_lab.get('population_split_available')}`",
        "",
        "## Swing Runtime Approval",
        f"- request_report: `{swing_runtime.get('request_report') or '-'}`",
        f"- approval_artifact: `{swing_runtime.get('approval_artifact') or '-'}`",
        f"- requested/approved/live_dry_run: `{swing_runtime.get('requested')}` / `{swing_runtime.get('approved')}` / `{swing_runtime.get('selected_live_dry_run')}`",
        f"- dry_run_forced: `{swing_runtime.get('dry_run_forced')}`",
        f"- real_canary_policy: `{((swing_runtime.get('real_canary_policy') or {}).get('policy_id')) or '-'}`",
        f"- real_order_allowed_actions: `{', '.join((swing_runtime.get('real_canary_policy') or {}).get('real_order_allowed_actions') or [])}`",
        f"- sim_only_actions: `{', '.join((swing_runtime.get('real_canary_policy') or {}).get('sim_only_actions') or [])}`",
        f"- scale_in_real_canary_policy: `{((swing_runtime.get('scale_in_real_canary_policy') or {}).get('policy_id')) or '-'}`",
        f"- selected_scale_in_real_canary: `{swing_runtime.get('selected_scale_in_real_canary')}`",
        f"- scale_in_real_execution_quality: `{swing_runtime.get('real_execution_quality') or {}}`",
        f"- blocked: `{swing_runtime.get('blocked') or []}`",
        "",
        "## Code Improvement Workorder",
        f"- artifact: `{code_workorder.get('artifact') or '-'}`",
        f"- markdown: `{code_workorder.get('markdown') or '-'}`",
        f"- selected_order_count: `{code_workorder.get('selected_order_count')}`",
        f"- decision_counts: `{code_workorder.get('decision_counts')}`",
        "",
        "## Approval Requests",
    ]
    if approval_requests:
        for item in approval_requests:
            if isinstance(item, dict):
                lines.append(
                    f"- `{item.get('family')}` sample=`{item.get('sample_count')}/{item.get('sample_floor')}` "
                    f"reason=`{item.get('calibration_reason')}`"
                )
    else:
        lines.append("- none")
    swing_requests = swing_runtime.get("requests") if isinstance(swing_runtime.get("requests"), list) else []
    lines.extend(["", "## Swing Approval Requests"])
    if swing_requests:
        for item in swing_requests:
            if isinstance(item, dict):
                lines.append(
                    f"- `{item.get('family')}` approval_id=`{item.get('approval_id')}` "
                    f"score=`{item.get('tradeoff_score')}` target_env_keys=`{item.get('target_env_keys')}`"
                )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Calibration Decisions",
        ]
    )
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
