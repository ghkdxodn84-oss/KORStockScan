"""Build a bounded daily Plan Rebase renewal proposal from postclose artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import PROJECT_ROOT


REPORT_DIR = PROJECT_ROOT / "data" / "report"
EV_REPORT_DIR = REPORT_DIR / "threshold_cycle_ev"
RUNTIME_APPROVAL_SUMMARY_DIR = REPORT_DIR / "runtime_approval_summary"
OPENAI_WS_REPORT_DIR = REPORT_DIR / "openai_ws"
SWING_RUNTIME_APPROVAL_DIR = REPORT_DIR / "swing_runtime_approval"
PLAN_REBASE_RENEWAL_DIR = REPORT_DIR / "plan_rebase_daily_renewal"

PLAN_REBASE_PATH = PROJECT_ROOT / "docs" / "plan-korStockScanPerformanceOptimization.rebase.md"
PROMPT_PATH = PROJECT_ROOT / "docs" / "plan-korStockScanPerformanceOptimization.prompt.md"
AGENTS_PATH = PROJECT_ROOT / "AGENTS.md"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _path_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
    }


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _summary_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _runtime_apply_state(ev_report: dict[str, Any]) -> dict[str, Any]:
    runtime = _summary_dict(ev_report.get("runtime_apply"))
    selected = [str(item) for item in _as_list(runtime.get("selected_families")) if str(item).strip()]
    return {
        "runtime_change": bool(runtime.get("runtime_change")) or bool(selected),
        "selected_families": selected,
        "apply_status": runtime.get("apply_status") or runtime.get("status") or "-",
        "runtime_env_file": runtime.get("runtime_env_file"),
    }


def _scalping_state(runtime_summary: dict[str, Any]) -> dict[str, Any]:
    rows = _as_list(runtime_summary.get("scalping"))
    return {
        "item_count": len(rows),
        "selected_auto_bounded_live": [
            str(row.get("family"))
            for row in rows
            if isinstance(row, dict) and bool(row.get("selected_auto_bounded_live"))
        ],
        "hold_or_blocked": [
            {
                "family": row.get("family"),
                "state": row.get("state"),
                "reason": row.get("reason_label"),
            }
            for row in rows
            if isinstance(row, dict) and not bool(row.get("selected_auto_bounded_live"))
        ][:10],
    }


def _swing_state(runtime_summary: dict[str, Any], swing_report: dict[str, Any]) -> dict[str, Any]:
    summary = _summary_dict(runtime_summary.get("summary"))
    swing_summary = _summary_dict(swing_report.get("summary"))
    requested = summary.get("swing_requested", swing_summary.get("requested", 0))
    approved = summary.get("swing_approved", swing_summary.get("approved", 0))
    return {
        "requested": int(requested or 0),
        "approved": int(approved or 0),
        "approval_artifact_required": int(requested or 0) > int(approved or 0),
        "runtime_effect": "dry_run_or_approval_required_only",
    }


def _panic_state(runtime_summary: dict[str, Any]) -> dict[str, Any]:
    summary = _summary_dict(runtime_summary.get("summary"))
    panic_rows = [
        row
        for row in _as_list(runtime_summary.get("panic"))
        if isinstance(row, dict)
    ]
    return {
        "approval_requested": int(summary.get("panic_approval_requested") or 0),
        "families": [str(row.get("family")) for row in panic_rows if row.get("family")],
        "runtime_effect": "approval_required_or_report_only",
    }


def _openai_state(openai_report: dict[str, Any]) -> dict[str, Any]:
    entry = _summary_dict(openai_report.get("entry_price_canary_summary"))
    return {
        "decision": openai_report.get("decision") or "missing",
        "entry_price_canary_event_count": int(entry.get("canary_event_count") or 0),
        "entry_price_transport_observable_count": int(entry.get("transport_observable_count") or 0),
        "entry_price_instrumentation_gap": bool(entry.get("instrumentation_gap")),
    }


def _warnings(sources: dict[str, dict[str, Any]], runtime_summary: dict[str, Any]) -> list[str]:
    warnings = [f"{name}_missing" for name, status in sources.items() if not status["exists"]]
    runtime_warnings = _as_list(runtime_summary.get("warnings"))
    warnings.extend(str(item) for item in runtime_warnings if str(item).strip())
    return sorted(set(warnings))


def build_plan_rebase_daily_renewal(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    ev_path = EV_REPORT_DIR / f"threshold_cycle_ev_{target_date}.json"
    runtime_path = RUNTIME_APPROVAL_SUMMARY_DIR / f"runtime_approval_summary_{target_date}.json"
    openai_path = OPENAI_WS_REPORT_DIR / f"openai_ws_stability_{target_date}.json"
    swing_path = SWING_RUNTIME_APPROVAL_DIR / f"swing_runtime_approval_{target_date}.json"

    ev_report = _load_json(ev_path)
    runtime_summary = _load_json(runtime_path)
    openai_report = _load_json(openai_path)
    swing_report = _load_json(swing_path)

    sources = {
        "threshold_cycle_ev": _path_status(ev_path),
        "runtime_approval_summary": _path_status(runtime_path),
        "openai_ws_stability": _path_status(openai_path),
        "swing_runtime_approval": _path_status(swing_path),
        "plan_rebase": _path_status(PLAN_REBASE_PATH),
        "prompt": _path_status(PROMPT_PATH),
        "agents": _path_status(AGENTS_PATH),
    }
    warnings = _warnings(sources, runtime_summary)
    renewal_state = "proposal_ready" if not warnings else "blocked_missing_or_warning_sources"

    report = {
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "plan_rebase_daily_renewal",
        "mode": "proposal_only",
        "runtime_mutation_allowed": False,
        "document_mutation_allowed": False,
        "renewal_state": renewal_state,
        "sources": sources,
        "warnings": warnings,
        "guardrails": {
            "allowed_update_scope": [
                "plan_rebase_current_date",
                "plan_rebase_current_runtime_state_summary",
                "prompt_source_of_truth_summary",
                "agents_current_state_snapshot",
            ],
            "forbidden_update_scope": [
                "metric_decision_contract",
                "rollback_guard_relaxation",
                "live_or_real_order_approval",
                "runtime_threshold_mutation",
                "archive_deletion",
            ],
            "apply_requires_explicit_flag": True,
            "default_apply_behavior": "no_file_mutation",
        },
        "proposal": {
            "plan_rebase": {
                "basis_date": f"{target_date} KST",
                "current_runtime_apply": _runtime_apply_state(ev_report),
                "open_state_summary": {
                    "scalping": _scalping_state(runtime_summary),
                    "swing": _swing_state(runtime_summary, swing_report),
                    "panic": _panic_state(runtime_summary),
                    "openai": _openai_state(openai_report),
                },
            },
            "prompt": {
                "basis_date": f"{target_date} KST",
                "source_of_truth": [
                    "plan-korStockScanPerformanceOptimization.rebase.md",
                    f"checklists/{target_date}-stage2-todo-checklist.md",
                    "report-based-automation-traceability.md",
                    "data/threshold_cycle/README.md",
                ],
            },
            "agents": {
                "current_state_basis": f"{target_date} KST",
                "selected_runtime_families": _runtime_apply_state(ev_report)["selected_families"],
                "must_remain_read_only": [
                    "sim_probe_counterfactual_real_order_authority",
                    "swing_approval_without_artifact",
                    "sentinel_panic_provider_or_order_mutation",
                ],
            },
        },
    }

    PLAN_REBASE_RENEWAL_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = PLAN_REBASE_RENEWAL_DIR / f"plan_rebase_daily_renewal_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def render_markdown(report: dict[str, Any]) -> str:
    proposal = _summary_dict(report.get("proposal"))
    plan = _summary_dict(proposal.get("plan_rebase"))
    runtime = _summary_dict(plan.get("current_runtime_apply"))
    open_state = _summary_dict(plan.get("open_state_summary"))
    lines = [
        f"# Plan Rebase Daily Renewal - {report.get('date')}",
        "",
        "- mode: `proposal_only`",
        "- runtime_mutation_allowed: `False`",
        "- document_mutation_allowed: `False`",
        f"- renewal_state: `{report.get('renewal_state')}`",
        f"- selected_runtime_families: `{', '.join(runtime.get('selected_families') or []) or '-'}`",
        "",
        "## Proposed Snapshot",
        "",
        f"- basis_date: `{plan.get('basis_date')}`",
        f"- runtime_change: `{runtime.get('runtime_change')}`",
        f"- openai_decision: `{_summary_dict(open_state.get('openai')).get('decision')}`",
        f"- swing_requested/approved: `{_summary_dict(open_state.get('swing')).get('requested')}` / `{_summary_dict(open_state.get('swing')).get('approved')}`",
        f"- panic_approval_requested: `{_summary_dict(open_state.get('panic')).get('approval_requested')}`",
        "",
        "## Guardrails",
        "",
    ]
    guardrails = _summary_dict(report.get("guardrails"))
    lines.append("- allowed_update_scope: `" + ", ".join(guardrails.get("allowed_update_scope") or []) + "`")
    lines.append("- forbidden_update_scope: `" + ", ".join(guardrails.get("forbidden_update_scope") or []) + "`")
    warnings = _as_list(report.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- `{warning}`" for warning in warnings)
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a proposal-only Plan Rebase daily renewal artifact.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_plan_rebase_daily_renewal(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
