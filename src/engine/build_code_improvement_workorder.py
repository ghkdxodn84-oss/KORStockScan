"""Build Codex-ready code improvement workorders from pattern lab automation."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
PATTERN_LAB_AUTOMATION_DIR = REPORT_DIR / "scalping_pattern_lab_automation"
THRESHOLD_CYCLE_EV_DIR = REPORT_DIR / "threshold_cycle_ev"
CODE_IMPROVEMENT_WORKORDER_DIR = PROJECT_ROOT / "docs" / "code-improvement-workorders"
CODE_IMPROVEMENT_WORKORDER_REPORT_DIR = REPORT_DIR / "code_improvement_workorder"
WORKORDER_SCHEMA_VERSION = 1


DECISION_RANK = {
    "implement_now": 0,
    "attach_existing_family": 1,
    "design_family_candidate": 2,
    "defer_evidence": 3,
    "reject": 4,
}


@dataclass(frozen=True)
class ClassifiedOrder:
    order: dict[str, Any]
    decision: str
    reason: str
    mapped_family: str | None
    route: str | None
    confidence: str | None
    automation_reentry: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:80] or "unknown"


def _next_calendar_day(target_date: str) -> str:
    try:
        return (date.fromisoformat(target_date) + timedelta(days=1)).isoformat()
    except ValueError:
        return target_date


def automation_report_path(target_date: str) -> Path:
    return PATTERN_LAB_AUTOMATION_DIR / f"scalping_pattern_lab_automation_{target_date}.json"


def threshold_ev_report_path(target_date: str) -> Path:
    return THRESHOLD_CYCLE_EV_DIR / f"threshold_cycle_ev_{target_date}.json"


def code_improvement_workorder_paths(target_date: str) -> tuple[Path, Path]:
    base = f"code_improvement_workorder_{target_date}"
    return (
        CODE_IMPROVEMENT_WORKORDER_REPORT_DIR / f"{base}.json",
        CODE_IMPROVEMENT_WORKORDER_DIR / f"{base}.md",
    )


def _finding_maps(report: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_order_id: dict[str, dict[str, Any]] = {}
    by_title_slug: dict[str, dict[str, Any]] = {}
    for section in ("consensus_findings", "solo_findings"):
        for finding in report.get(section) or []:
            if not isinstance(finding, dict):
                continue
            finding_id = str(finding.get("finding_id") or "").strip()
            title = str(finding.get("title") or "").strip()
            if finding_id:
                by_order_id[f"order_{finding_id}"] = finding
            if title:
                by_title_slug[_slug(title)] = finding
    return by_order_id, by_title_slug


def _auto_family_order_ids(report: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for item in report.get("auto_family_candidates") or []:
        if not isinstance(item, dict):
            continue
        implementation_id = str(item.get("implementation_order_id") or "").strip()
        if implementation_id:
            result.add(implementation_id)
        family_id = str(item.get("family_id") or "").strip()
        if family_id:
            result.add(f"order_{family_id}")
    return result


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(token in lower for token in tokens)


def _classify_order(
    order: dict[str, Any],
    *,
    finding_by_order_id: dict[str, dict[str, Any]],
    finding_by_title_slug: dict[str, dict[str, Any]],
    auto_family_order_ids: set[str],
) -> ClassifiedOrder:
    order_id = str(order.get("order_id") or "").strip()
    title = str(order.get("title") or "").strip()
    subsystem = str(order.get("target_subsystem") or "").strip()
    text = f"{order_id} {title} {subsystem}"
    finding = finding_by_order_id.get(order_id) or finding_by_title_slug.get(_slug(title)) or {}
    route = str(finding.get("route") or "").strip() or None
    mapped_family = str(finding.get("mapped_family") or "").strip() or None
    confidence = str(finding.get("confidence") or "").strip() or None

    if bool(order.get("runtime_effect")):
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason="pattern lab order must remain runtime_effect=false; runtime_effect=true is treated as artifact error",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Reject artifact and regenerate pattern lab automation before implementation.",
        )

    if _contains_any(text, ("fallback", "shadow")):
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason="fallback revival or shadow reintroduction conflicts with current Plan Rebase policy",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Keep as rejected finding unless translated into report_only_calibration or bounded canary design.",
        )

    if confidence == "solo":
        return ClassifiedOrder(
            order=order,
            decision="defer_evidence",
            reason="single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Re-evaluate in the next postclose pattern lab automation and daily EV report.",
        )

    if subsystem == "runtime_instrumentation" or route == "instrumentation_order":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="instrumentation/provenance work can improve attribution without direct runtime mutation",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="After implementation, next postclose report must show source freshness or warning reduction.",
        )

    if route == "existing_family" or mapped_family:
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason="finding maps to an existing threshold family and should strengthen source metrics/provenance",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="After implementation, intraday/postclose calibration should include the updated family input.",
        )

    if route == "auto_family_candidate" or order_id in auto_family_order_ids:
        return ClassifiedOrder(
            order=order,
            decision="design_family_candidate",
            reason="finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Create report-only family metadata first; only later can auto_bounded_live consider it.",
        )

    return ClassifiedOrder(
        order=order,
        decision="defer_evidence",
        reason="route is not strong enough for immediate implementation",
        mapped_family=mapped_family,
        route=route,
        confidence=confidence,
        automation_reentry="Keep in generated workorder as deferred context and re-check after next daily EV report.",
    )


def _sort_classified(items: list[ClassifiedOrder]) -> list[ClassifiedOrder]:
    return sorted(
        items,
        key=lambda item: (
            DECISION_RANK.get(item.decision, 99),
            _safe_int(item.order.get("priority"), 999),
            str(item.order.get("order_id") or ""),
        ),
    )


def build_code_improvement_workorder(target_date: str, *, max_orders: int = 12) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_path = automation_report_path(target_date)
    automation = _load_json(source_path)
    ev_path = threshold_ev_report_path(target_date)
    ev_report = _load_json(ev_path)
    finding_by_order_id, finding_by_title_slug = _finding_maps(automation)
    auto_family_ids = _auto_family_order_ids(automation)
    orders = [item for item in (automation.get("code_improvement_orders") or []) if isinstance(item, dict)]
    classified = _sort_classified(
        [
            _classify_order(
                order,
                finding_by_order_id=finding_by_order_id,
                finding_by_title_slug=finding_by_title_slug,
                auto_family_order_ids=auto_family_ids,
            )
            for order in orders
        ]
    )
    selected = classified[: max(1, int(max_orders))]
    counts: dict[str, int] = {}
    for item in classified:
        counts[item.decision] = counts.get(item.decision, 0) + 1
    report = {
        "schema_version": WORKORDER_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "purpose": "codex_code_improvement_workorder_from_pattern_lab",
        "source": {
            "pattern_lab_automation": str(source_path),
            "threshold_cycle_ev": str(ev_path) if ev_path.exists() else None,
        },
        "policy": {
            "runtime_patch_automation": False,
            "user_intervention_point": "paste generated markdown into a Codex session and request implementation",
            "post_implementation_reentry": "postclose reports and daily EV consume the updated source metrics automatically",
        },
        "summary": {
            "source_order_count": len(orders),
            "selected_order_count": len(selected),
            "decision_counts": counts,
            "gemini_fresh": ((automation.get("ev_report_summary") or {}).get("gemini_fresh")),
            "claude_fresh": ((automation.get("ev_report_summary") or {}).get("claude_fresh")),
            "daily_ev_available": bool(ev_report),
        },
        "orders": [
            {
                "order_id": item.order.get("order_id"),
                "title": item.order.get("title"),
                "target_subsystem": item.order.get("target_subsystem"),
                "priority": item.order.get("priority"),
                "decision": item.decision,
                "decision_reason": item.reason,
                "route": item.route,
                "mapped_family": item.mapped_family,
                "confidence": item.confidence,
                "intent": item.order.get("intent"),
                "expected_ev_effect": item.order.get("expected_ev_effect"),
                "files_likely_touched": item.order.get("files_likely_touched") or [],
                "acceptance_tests": item.order.get("acceptance_tests") or [],
                "automation_reentry": item.automation_reentry,
                "runtime_effect": bool(item.order.get("runtime_effect")),
            }
            for item in selected
        ],
        "deferred_or_rejected_count": max(0, len(classified) - len(selected)),
        "next_codex_session": {
            "instruction": "Paste the generated markdown into Codex and ask: '이 code improvement workorder를 순서대로 구현하고 검증해줘.'",
            "workorder_markdown": str(code_improvement_workorder_paths(target_date)[1]),
        },
    }
    json_path, md_path = code_improvement_workorder_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_code_improvement_workorder_markdown(report), encoding="utf-8")
    return report


def _format_list(values: Any) -> str:
    items = [str(item) for item in (values or []) if str(item).strip()]
    return ", ".join(f"`{item}`" for item in items) if items else "-"


def render_code_improvement_workorder_markdown(report: dict[str, Any]) -> str:
    date_value = report.get("date") or ""
    next_date = _next_calendar_day(str(date_value))
    source = report.get("source") if isinstance(report.get("source"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    policy = report.get("policy") if isinstance(report.get("policy"), dict) else {}
    lines = [
        f"# Code Improvement Workorder - {date_value}",
        "",
        "## 목적",
        "",
        "- Pattern lab이 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.",
        "- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.",
        "- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.",
        "",
        "## Source",
        "",
        f"- pattern_lab_automation: `{source.get('pattern_lab_automation')}`",
        f"- threshold_cycle_ev: `{source.get('threshold_cycle_ev') or '-'}`",
        f"- generated_at: `{report.get('generated_at')}`",
        "",
        "## 운영 원칙",
        "",
        "- `runtime_effect=false` order만 구현 대상으로 본다.",
        "- fallback 재개, shadow 재개, safety guard 우회는 구현하지 않는다.",
        "- runtime 영향이 생길 수 있는 변경은 feature flag, threshold family metadata, provenance, safety guard를 같이 닫는다.",
        "- 새 family는 `allowed_runtime_apply=false`에서 시작하고, 구현/테스트/guard 완료 후에만 auto_bounded_live 후보가 될 수 있다.",
        "- 구현 후에는 관련 테스트와 parser 검증을 실행하고, 다음 postclose daily EV에서 metric을 확인한다.",
        "",
        "## Summary",
        "",
        f"- source_order_count: `{summary.get('source_order_count')}`",
        f"- selected_order_count: `{summary.get('selected_order_count')}`",
        f"- decision_counts: `{summary.get('decision_counts')}`",
        f"- gemini_fresh: `{summary.get('gemini_fresh')}`",
        f"- claude_fresh: `{summary.get('claude_fresh')}`",
        f"- daily_ev_available: `{summary.get('daily_ev_available')}`",
        "",
        "## Codex 실행 지시",
        "",
        "아래 order를 위에서부터 순서대로 처리한다. 각 order는 `판정 -> 근거 -> 다음 액션`으로 닫고, 코드 변경 시 관련 문서와 테스트를 함께 갱신한다.",
        "",
        "필수 검증:",
        "",
        "```bash",
        "PYTHONPATH=. .venv/bin/pytest -q <관련 테스트 파일>",
        "PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500",
        "git diff --check",
        "```",
        "",
        "threshold/postclose 체인 영향 시 추가 검증:",
        "",
        "```bash",
        "bash -n deploy/run_threshold_cycle_preopen.sh deploy/run_threshold_cycle_calibration.sh deploy/run_threshold_cycle_postclose.sh",
        "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_threshold_cycle_ev_report.py",
        "```",
        "",
        "## Implementation Orders",
        "",
    ]
    for index, item in enumerate(report.get("orders") or [], start=1):
        if not isinstance(item, dict):
            continue
        lines.extend(
            [
                f"### {index}. `{item.get('order_id')}`",
                "",
                f"- title: {item.get('title')}",
                f"- decision: `{item.get('decision')}`",
                f"- decision_reason: {item.get('decision_reason')}",
                f"- target_subsystem: `{item.get('target_subsystem')}`",
                f"- route: `{item.get('route') or '-'}`",
                f"- mapped_family: `{item.get('mapped_family') or '-'}`",
                f"- confidence: `{item.get('confidence') or '-'}`",
                f"- priority: `{item.get('priority')}`",
                f"- runtime_effect: `{item.get('runtime_effect')}`",
                f"- expected_ev_effect: {item.get('expected_ev_effect')}",
                f"- files_likely_touched: {_format_list(item.get('files_likely_touched'))}",
                f"- acceptance_tests: {_format_list(item.get('acceptance_tests'))}",
                f"- automation_reentry: {item.get('automation_reentry')}",
                "",
                "실행 기준:",
                "",
            ]
        )
        decision = item.get("decision")
        if decision == "implement_now":
            lines.extend(
                [
                    "- instrumentation/provenance/report source 보강을 우선 구현한다.",
                    "- runtime 판단값을 직접 바꾸지 않는다.",
                    "- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.",
                    "",
                ]
            )
        elif decision == "attach_existing_family":
            lines.extend(
                [
                    "- 기존 threshold family의 source metric/provenance를 보강한다.",
                    "- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.",
                    "- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.",
                    "",
                ]
            )
        elif decision == "design_family_candidate":
            lines.extend(
                [
                    "- 새 family 후보 metadata와 report-only source를 설계한다.",
                    "- `allowed_runtime_apply=false`를 유지한다.",
                    "- sample floor, safety guard, target env key, tests가 닫히기 전 runtime 적용 금지.",
                    "",
                ]
            )
        elif decision == "defer_evidence":
            lines.extend(
                [
                    "- 구현하지 말고 부족한 evidence와 다음 확인 artifact를 명시한다.",
                    "- 필요한 경우 report warning 또는 다음 pattern lab 재평가 항목으로만 남긴다.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "- 구현하지 않는다.",
                    "- reject 사유를 유지하고, 필요하면 report_only_calibration 또는 bounded canary 설계로 번역 가능한지 별도 판단한다.",
                    "",
                ]
            )
    if not report.get("orders"):
        lines.append("- none")
        lines.append("")
    lines.extend(
        [
            "## 자동화체인 재투입",
            "",
            f"- 구현 결과는 `{next_date}` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.",
            "- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.",
            f"- 다음 Codex 세션 입력 문구: `{policy.get('user_intervention_point')}`",
            "",
            "## Project/Calendar 동기화",
            "",
            "문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.",
            "",
            "```bash",
            "PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Codex code improvement workorder from pattern lab automation.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--max-orders", type=int, default=12)
    args = parser.parse_args(argv)
    report = build_code_improvement_workorder(args.target_date, max_orders=args.max_orders)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
