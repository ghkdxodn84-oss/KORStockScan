from __future__ import annotations

import os
import time
from datetime import datetime, date
from pathlib import Path
from typing import Any

from src.utils.constants import PROJECT_ROOT, TRADING_RULES
from src.utils.market_day import is_krx_trading_day

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)


def _today_kst_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


ARTIFACT_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "pipeline_events",
        "path_template": "data/pipeline_events/pipeline_events_{date}.jsonl",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
    },
    {
        "id": "threshold_events",
        "path_template": "data/threshold_cycle/threshold_events_{date}.jsonl",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
    },
    {
        "id": "daily_recommendations_csv",
        "path_template": "data/daily_recommendations_v2.csv",
        "max_staleness_sec": 3600,
        "critical": False,
        "window_start": (7, 20),
        "window_end": (8, 0),
        "trading_day_only": True,
    },
    {
        "id": "daily_recommendations_diag",
        "path_template": "data/daily_recommendations_v2_diagnostics.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "window_start": (7, 20),
        "window_end": (8, 0),
        "trading_day_only": True,
    },
    {
        "id": "threshold_runtime_env",
        "path_template": "data/threshold_cycle/runtime_env/threshold_runtime_env_{date}.json",
        "max_staleness_sec": 900,
        "critical": True,
        "window_start": (7, 35),
        "window_end": (7, 50),
        "trading_day_only": True,
    },
    {
        "id": "threshold_apply_plan",
        "path_template": "data/threshold_cycle/apply_plans/threshold_apply_{date}.json",
        "max_staleness_sec": 900,
        "critical": True,
        "window_start": (7, 35),
        "window_end": (7, 50),
        "trading_day_only": True,
    },
    {
        "id": "buy_funnel_sentinel_report",
        "path_template": "data/report/buy_funnel_sentinel/buy_funnel_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "holding_exit_sentinel_report",
        "path_template": "data/report/holding_exit_sentinel/holding_exit_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "threshold_postclose_report",
        "path_template": "data/report/threshold_cycle_ev/threshold_cycle_ev_{date}.json",
        "max_staleness_sec": 1800,
        "critical": True,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 0),
    },
    {
        "id": "code_improvement_workorder",
        "path_template": "docs/code-improvement-workorders/code_improvement_workorder_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 0),
    },
]


@register_detector
class ArtifactFreshnessDetector(BaseDetector):
    id = "artifact_freshness"
    name = "Artifact Freshness Detector"
    category = "artifact"

    def check(self) -> DetectionResult:
        now_ts = time.time()
        now_h, now_m = _kst_time_tuple()
        now_total = now_h * 60 + now_m
        today = _today_kst_str()
        trading_day = is_krx_trading_day(datetime.now().date())
        details: dict = {}
        issues: list[str] = []
        warnings: list[str] = []

        for artifact in ARTIFACT_REGISTRY:
            aid = artifact["id"]
            path_str = artifact["path_template"].replace("{date}", today)
            artifact_path = PROJECT_ROOT / path_str
            critical = artifact.get("critical", False)
            max_stale = artifact.get("max_staleness_sec", 600)
            trading_day_only = artifact.get("trading_day_only", False)
            ws = artifact.get("window_start")
            we = artifact.get("window_end")

            if trading_day_only and not trading_day:
                details[f"{aid}_status"] = "skip_non_trading_day"
                continue

            ws_total = ws[0] * 60 + ws[1] if ws else None
            we_total = we[0] * 60 + we[1] if we else None

            if ws_total is not None and now_total < ws_total:
                details[f"{aid}_status"] = "not_yet_due"
                details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                continue

            past_window_end = we_total is not None and now_total > we_total

            exists = artifact_path.exists()

            if not exists:
                if past_window_end:
                    if critical:
                        issues.append(f"{aid}: missing after window end")
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(f"{aid}: not generated within window")
                        details[f"{aid}_status"] = "warning"
                else:
                    if critical:
                        issues.append(f"{aid}: {path_str} missing")
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(f"{aid}: {path_str} not found")
                        details[f"{aid}_status"] = "warning"
                continue

            mtime = artifact_path.stat().st_mtime
            age_sec = now_ts - mtime
            details[f"{aid}_age_sec"] = round(age_sec, 1)

            if past_window_end:
                details[f"{aid}_status"] = "pass_after_window"
                continue

            if age_sec > max_stale:
                if critical:
                    issues.append(f"{aid}: stale ({age_sec:.0f}s > {max_stale}s)")
                    details[f"{aid}_status"] = "fail"
                else:
                    warnings.append(f"{aid}: stale ({age_sec:.0f}s > {max_stale}s)")
                    details[f"{aid}_status"] = "warning"
            else:
                details[f"{aid}_status"] = "pass"

        severity, summary = self._classify(issues, warnings)
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity=severity,
            summary=summary,
            details=details,
            recommended_action=self._recommend_action(severity, issues),
        )

    @staticmethod
    def _classify(issues: list[str], warnings: list[str]) -> tuple[str, str]:
        if issues:
            return "fail", f"Artifact failures: {'; '.join(issues[:5])}"
        if warnings:
            return "warning", f"Artifact warnings: {'; '.join(warnings[:5])}"
        return "pass", "All critical artifacts fresh."

    @staticmethod
    def _recommend_action(severity: str, issues: list[str]) -> str:
        if severity == "fail":
            return f"Check missing/stale artifacts: {'; '.join(issues[:3])}"
        if severity == "warning":
            return "Non-critical artifacts missing/stale. Monitor next cycle."
        return ""


def _kst_time_tuple() -> tuple[int, int]:
    now_kst = datetime.now()
    return now_kst.hour, now_kst.minute
