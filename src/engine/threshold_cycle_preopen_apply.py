"""Build a preopen threshold apply manifest from the latest postclose report."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils.constants import DATA_DIR


APPLY_PLAN_DIR = DATA_DIR / "threshold_cycle" / "apply_plans"


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
    if not candidates:
        return None
    return sorted(candidates)[-1][1]


def apply_manifest_path(target_date: str) -> Path:
    return APPLY_PLAN_DIR / f"threshold_apply_{target_date}.json"


def _report_path_for_date(target_date: str) -> Path:
    return REPORT_DIR / f"threshold_cycle_{target_date}.json"


def build_preopen_apply_manifest(
    target_date: str,
    *,
    source_date: str | None = None,
    apply_mode: str = "manifest_only",
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
        status = (
            "efficient_tradeoff_manifest_ready"
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
            "runtime_change": False,
            "runtime_change_reason": (
                "장중 자동 mutation 금지; calibrated/efficient trade-off 후보도 승인된 family의 다음 장전 bounded apply 후보만 생성"
            ),
            "candidates": candidates,
            "calibration_candidates": calibration_candidates,
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
            },
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
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
        choices=["manifest_only", "calibrated_apply_candidate", "efficient_tradeoff_canary_candidate"],
        help="Apply mode. Runtime mutation is unavailable; calibrated modes emit bounded next-preopen candidates.",
    )
    args = parser.parse_args(argv)
    manifest = build_preopen_apply_manifest(args.target_date, source_date=args.source_date, apply_mode=args.apply_mode)
    print(json.dumps(manifest, ensure_ascii=False))
    return 0 if manifest.get("status") in {"manifest_ready", "calibrated_manifest_ready", "efficient_tradeoff_manifest_ready"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
