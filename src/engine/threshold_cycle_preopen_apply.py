"""Build a preopen threshold apply manifest from the latest postclose report."""

from __future__ import annotations

import argparse
import json
import os
import shlex
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils.constants import DATA_DIR


APPLY_PLAN_DIR = DATA_DIR / "threshold_cycle" / "apply_plans"
RUNTIME_ENV_DIR = DATA_DIR / "threshold_cycle" / "runtime_env"
AI_REVIEW_DIR = REPORT_DIR / "threshold_cycle_ai_review"
CALIBRATION_REPORT_DIR = REPORT_DIR / "threshold_cycle_calibration"

AUTO_APPLY_MODES = {"auto_bounded_live"}
AUTO_APPLY_ALLOWED_STATES = {"adjust_up", "adjust_down", "hold"}
AUTO_APPLY_BLOCK_STATES = {"freeze", "hold_sample", "hold_no_edge"}
AUTO_APPLY_ROUTE_EXCLUDE_ACTIONS = {"exclude_from_threshold_candidate_review"}
AUTO_APPLY_ALLOWED_ROUTES = {"threshold_candidate", "normal_drift", ""}

TARGET_ENV_VALUE_KEYS = {
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "enabled",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC": "confirm_sec",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT": "buffer_pct",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT": "max_worsen_pct",
    "AI_SCORE65_74_RECOVERY_PROBE_ENABLED": "enabled",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE": "min_score",
    "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE": "max_score",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE": "min_buy_pressure",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL": "min_tick_accel",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP": "min_micro_vwap_bp",
    "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW": "max_budget_krw",
    "AI_WAIT6579_PROBE_CANARY_MAX_QTY": "max_qty",
    "SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED": "enabled",
    "SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC": "min_hold_sec",
    "SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT": "min_loss_pct",
    "SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT": "max_peak_profit_pct",
    "SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT": "ai_score_limit",
    "SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX": "recovery_prob_max",
    "OFI_AI_SMOOTHING_STALE_THRESHOLD_MS": "ofi_stale_threshold_ms",
    "OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED": "ofi_persistence_required",
    "HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT": "holding_bearish_confirm_worsen_pct",
    "HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC": "max_defer_sec",
    "HOLDING_FLOW_OVERRIDE_WORSEN_PCT": "worsen_floor_pct",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _latest_report_before(target_date: str) -> Path | None:
    candidates: list[tuple[str, Path]] = []
    for path in REPORT_DIR.glob("threshold_cycle_*.json"):
        report_date = path.stem.replace("threshold_cycle_", "")
        if report_date < target_date:
            candidates.append((report_date, path))
    for path in CALIBRATION_REPORT_DIR.glob("threshold_cycle_calibration_*_postclose.json"):
        report_date = path.stem.replace("threshold_cycle_calibration_", "").replace("_postclose", "")
        if report_date < target_date:
            candidates.append((report_date, path))
    if not candidates:
        return None
    return sorted(candidates)[-1][1]


def apply_manifest_path(target_date: str) -> Path:
    return APPLY_PLAN_DIR / f"threshold_apply_{target_date}.json"


def runtime_env_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.env"


def runtime_env_manifest_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.json"


def _report_path_for_date(target_date: str) -> Path:
    canonical = REPORT_DIR / f"threshold_cycle_{target_date}.json"
    if canonical.exists():
        return canonical
    postclose = CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_postclose.json"
    if postclose.exists():
        return postclose
    intraday = CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_intraday.json"
    if intraday.exists():
        return intraday
    return canonical


def _ai_review_path_for_date(source_date: str, phase: str) -> Path:
    return AI_REVIEW_DIR / f"threshold_cycle_ai_review_{source_date}_{phase}.json"


def _load_ai_review(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"status": "missing_source_date", "path": None, "items_by_family": {}}
    preferred_paths = [_ai_review_path_for_date(source_date, "postclose"), _ai_review_path_for_date(source_date, "intraday")]
    fallback_payload: dict[str, Any] | None = None
    fallback_path: Path | None = None
    for path in preferred_paths:
        if not path.exists():
            continue
        payload = _load_json(path)
        if str(payload.get("ai_status") or "").lower() != "parsed":
            fallback_payload = payload
            fallback_path = path
            continue
        items = payload.get("items") if isinstance(payload.get("items"), list) else []
        return {
            "status": str(payload.get("ai_status") or "unknown"),
            "path": str(path),
            "phase": path.stem.rsplit("_", 1)[-1],
            "model": payload.get("ai_model"),
            "provider_status": payload.get("ai_provider_status") or {},
            "items_by_family": {
                str(item.get("family") or ""): item for item in items if isinstance(item, dict) and item.get("family")
            },
        }
    if fallback_payload is not None and fallback_path is not None:
        items = fallback_payload.get("items") if isinstance(fallback_payload.get("items"), list) else []
        return {
            "status": str(fallback_payload.get("ai_status") or "unknown"),
            "path": str(fallback_path),
            "phase": fallback_path.stem.rsplit("_", 1)[-1],
            "model": fallback_payload.get("ai_model"),
            "provider_status": fallback_payload.get("ai_provider_status") or {},
            "items_by_family": {
                str(item.get("family") or ""): item for item in items if isinstance(item, dict) and item.get("family")
            },
        }
    return {"status": "missing_ai_review", "path": None, "items_by_family": {}}


def _runtime_env_name(target_env_key: str) -> str:
    if target_env_key.startswith("AI_SCORE65_74_RECOVERY_PROBE_"):
        return f"KORSTOCKSCAN_{target_env_key.removeprefix('AI_')}"
    if target_env_key.startswith("AI_WAIT6579_PROBE_CANARY_"):
        return f"KORSTOCKSCAN_{target_env_key.removeprefix('AI_')}"
    return f"KORSTOCKSCAN_{target_env_key}"


def _format_env_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) == bool(right)
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return str(left) == str(right)


def _env_overrides_for_candidate(candidate: dict[str, Any]) -> dict[str, str]:
    recommended = candidate.get("recommended_values") if isinstance(candidate.get("recommended_values"), dict) else {}
    current = candidate.get("current_values") if isinstance(candidate.get("current_values"), dict) else {}
    calibration_state = str(candidate.get("calibration_state") or "")
    overrides: dict[str, str] = {}
    for target_key in candidate.get("target_env_keys") or []:
        target_key = str(target_key)
        value_key = TARGET_ENV_VALUE_KEYS.get(target_key)
        if not value_key or value_key not in recommended:
            continue
        value = recommended[value_key]
        if value_key == "enabled" and calibration_state == "adjust_up" and not bool(current.get(value_key)):
            value = True
        if _values_equal(current.get(value_key), value):
            continue
        overrides[_runtime_env_name(target_key)] = _format_env_value(value)
    return overrides


def _ai_guard_allows_candidate(candidate: dict[str, Any], ai_review: dict[str, Any], *, require_ai: bool) -> tuple[bool, str]:
    items_by_family = ai_review.get("items_by_family") if isinstance(ai_review.get("items_by_family"), dict) else {}
    item = items_by_family.get(str(candidate.get("family") or ""))
    if not item:
        return (not require_ai, "ai_review_missing" if require_ai else "ai_review_missing_deterministic_allowed")
    if str(item.get("guard_decision") or "").lower() != "accept" and not bool(item.get("guard_accepted")):
        return (False, str(item.get("guard_reject_reason") or "ai_guard_rejected"))
    if str(item.get("route_action") or "") in AUTO_APPLY_ROUTE_EXCLUDE_ACTIONS:
        return (False, "ai_route_excluded_from_threshold_candidate")
    route = str(item.get("ai_anomaly_route") or "")
    if route not in AUTO_APPLY_ALLOWED_ROUTES:
        return (False, f"ai_route_not_runtime_apply:{route}")
    return (True, "ai_guard_accepted")


def _select_auto_apply_candidates(
    calibration_candidates: list[dict[str, Any]],
    *,
    ai_review: dict[str, Any],
    require_ai: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    selected_by_stage: dict[str, dict[str, Any]] = {}
    decisions: list[dict[str, Any]] = []
    for candidate in sorted(calibration_candidates, key=lambda item: int(item.get("priority") or 999)):
        family = str(candidate.get("family") or "")
        stage = str(candidate.get("stage") or "unknown")
        state = str(candidate.get("calibration_state") or "")
        allowed, reason = _ai_guard_allows_candidate(candidate, ai_review, require_ai=require_ai)
        reject_reason = ""
        if not bool(candidate.get("allowed_runtime_apply")):
            reject_reason = "runtime_apply_not_allowed"
        elif bool(candidate.get("safety_revert_required")):
            reject_reason = "safety_revert_required"
        elif state in AUTO_APPLY_BLOCK_STATES or state not in AUTO_APPLY_ALLOWED_STATES:
            reject_reason = f"calibration_state_blocked:{state}"
        elif not allowed:
            reject_reason = reason
        elif not _env_overrides_for_candidate(candidate):
            reject_reason = "no_runtime_env_override"
        elif stage in selected_by_stage:
            reject_reason = f"same_stage_owner_conflict:{selected_by_stage[stage].get('family')}"

        decision = {
            "family": family,
            "stage": stage,
            "priority": int(candidate.get("priority") or 999),
            "calibration_state": state,
            "threshold_version": candidate.get("threshold_version"),
            "selected": not bool(reject_reason),
            "decision_reason": reject_reason or reason,
            "env_overrides": _env_overrides_for_candidate(candidate) if not reject_reason else {},
        }
        if reject_reason:
            decisions.append(decision)
            continue
        selected_by_stage[stage] = candidate
        decisions.append(decision)

    selected_decisions = [decision for decision in decisions if bool(decision.get("selected"))]
    env_overrides: dict[str, str] = {}
    for decision in selected_decisions:
        env_overrides.update(decision.get("env_overrides") or {})
    return selected_decisions, decisions, env_overrides


def _write_runtime_env(target_date: str, manifest: dict[str, Any], env_overrides: dict[str, str]) -> None:
    RUNTIME_ENV_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Generated by threshold_cycle_preopen_apply.py",
        f"# target_date={target_date}",
        f"# source_date={manifest.get('source_date')}",
        f"# generated_at={manifest.get('generated_at')}",
        "export KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true",
        f"export KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE={shlex.quote(target_date)}",
    ]
    for key in sorted(env_overrides):
        lines.append(f"export {key}={shlex.quote(str(env_overrides[key]))}")
    runtime_env_path(target_date).write_text("\n".join(lines) + "\n", encoding="utf-8")
    runtime_env_manifest_path(target_date).write_text(
        json.dumps(
            {
                "target_date": target_date,
                "source_date": manifest.get("source_date"),
                "source_report": manifest.get("source_report"),
                "generated_at": manifest.get("generated_at"),
                "env_file": str(runtime_env_path(target_date)),
                "env_overrides": env_overrides,
                "selected_families": [item.get("family") for item in manifest.get("auto_apply_selected") or []],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def build_preopen_apply_manifest(
    target_date: str,
    *,
    source_date: str | None = None,
    apply_mode: str = "manifest_only",
    auto_apply: bool = False,
    require_ai: bool = True,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_path = _report_path_for_date(source_date) if source_date else _latest_report_before(target_date)
    if source_path is None or not source_path.exists():
        manifest = {
            "target_date": target_date,
            "status": "missing_source_report",
            "apply_mode": apply_mode,
            "runtime_change": False,
            "source_report": None,
            "candidates": [],
            "calibration_candidates": [],
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
    else:
        report = _load_json(source_path)
        candidates = report.get("apply_candidate_list") if isinstance(report.get("apply_candidate_list"), list) else []
        calibration_candidates = (
            report.get("calibration_candidates") if isinstance(report.get("calibration_candidates"), list) else []
        )
        auto_apply_requested = bool(auto_apply) or apply_mode in AUTO_APPLY_MODES
        ai_review = _load_ai_review(str(report.get("date") or source_date or ""))
        selected, decisions, env_overrides = ([], [], {})
        if auto_apply_requested:
            selected, decisions, env_overrides = _select_auto_apply_candidates(
                calibration_candidates,
                ai_review=ai_review,
                require_ai=require_ai,
            )
        runtime_change = bool(auto_apply_requested and env_overrides)
        status = (
            "auto_bounded_live_ready"
            if runtime_change
            else "auto_bounded_live_blocked"
            if auto_apply_requested
            else "efficient_tradeoff_manifest_ready"
            if apply_mode == "efficient_tradeoff_canary_candidate"
            else "calibrated_manifest_ready"
            if apply_mode == "calibrated_apply_candidate"
            else "manifest_ready"
        )
        manifest = {
            "target_date": target_date,
            "source_date": report.get("date"),
            "source_report": str(source_path),
            "status": status,
            "apply_mode": apply_mode,
            "runtime_change": runtime_change,
            "runtime_change_reason": (
                "장전 자동 bounded env apply; 장중 threshold mutation은 계속 금지"
                if runtime_change
                else "장전 자동 bounded env apply 후보 없음; 장중 threshold mutation은 계속 금지"
                if auto_apply_requested
                else "장중 자동 mutation 금지; calibrated/efficient trade-off 후보도 승인된 family의 다음 장전 bounded apply 후보만 생성"
            ),
            "candidates": candidates,
            "calibration_candidates": calibration_candidates,
            "ai_correction_review": {
                "required": bool(require_ai),
                "status": ai_review.get("status"),
                "path": ai_review.get("path"),
                "phase": ai_review.get("phase"),
                "model": ai_review.get("model"),
                "provider_status": ai_review.get("provider_status") or {},
            },
            "auto_apply_selected": selected,
            "auto_apply_decisions": decisions,
            "runtime_env_file": str(runtime_env_path(target_date)) if runtime_change else None,
            "runtime_env_overrides": env_overrides,
            "threshold_snapshot": report.get("threshold_snapshot") or {},
            "post_apply_attribution": report.get("post_apply_attribution") or {},
            "safety_guard_pack": report.get("safety_guard_pack") or [],
            "calibration_trigger_pack": report.get("calibration_trigger_pack") or [],
            "rollback_guard_pack": report.get("rollback_guard_pack") or [],
            "calibration_policy": {
                "condition_miss_action": "calibration_trigger",
                "sample_shortfall_action": "cap_reduce_or_hold_sample_or_max_step_shrink",
                "rollback_policy": "safety_breach_only",
                "intraday_runtime_mutation": False,
                "apply_frequency": "next_preopen_once",
                "human_approval_required": False,
                "ai_correction_required": bool(require_ai),
                "same_stage_owner_rule": "one_selected_family_per_stage_by_priority",
                "daily_ev_report_only": True,
            },
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        if runtime_change:
            _write_runtime_env(target_date, manifest, env_overrides)
    APPLY_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    apply_manifest_path(target_date).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build preopen threshold apply manifest.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat(), help="Target preopen date")
    parser.add_argument("--source-date", dest="source_date", default=None, help="Postclose report date to apply")
    parser.add_argument(
        "--apply-mode",
        default=os.getenv("THRESHOLD_CYCLE_APPLY_MODE", "manifest_only"),
        choices=[
            "manifest_only",
            "calibrated_apply_candidate",
            "efficient_tradeoff_canary_candidate",
            "auto_bounded_live",
        ],
        help="Apply mode. auto_bounded_live writes next-preopen runtime env under deterministic/AI guards.",
    )
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        default=str(os.getenv("THRESHOLD_CYCLE_AUTO_APPLY", "")).lower() in {"1", "true", "yes", "on"},
        help="Write guarded runtime env overrides for selected candidates.",
    )
    parser.add_argument(
        "--allow-deterministic-without-ai",
        action="store_true",
        default=str(os.getenv("THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI", "true")).lower() in {"0", "false", "no", "off"},
        help="Allow deterministic guards to apply when AI correction review is missing/unavailable.",
    )
    args = parser.parse_args(argv)
    manifest = build_preopen_apply_manifest(
        args.target_date,
        source_date=args.source_date,
        apply_mode=args.apply_mode,
        auto_apply=args.auto_apply,
        require_ai=not args.allow_deterministic_without_ai,
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return (
        0
        if manifest.get("status")
        in {
            "manifest_ready",
            "calibrated_manifest_ready",
            "efficient_tradeoff_manifest_ready",
            "auto_bounded_live_ready",
            "auto_bounded_live_blocked",
        }
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
