from __future__ import annotations

import json
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


def _today_kst_str(now_kst: datetime | None = None) -> str:
    return (now_kst or datetime.now()).strftime("%Y-%m-%d")


ARTIFACT_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "pipeline_events",
        "path_template": "data/pipeline_events/pipeline_events_{date}.jsonl",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
        "window_grace_sec": 300,
    },
    {
        "id": "threshold_events",
        "path_template": "data/threshold_cycle/threshold_events_{date}.jsonl",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
        "window_grace_sec": 300,
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
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 0),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
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
    {
        "id": "system_metric_samples",
        "path_template": "logs/system_metric_samples.jsonl",
        "max_staleness_sec": 180,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
    },
    {
        "id": "swing_live_dry_run_status",
        "path_template": "data/report/swing_selection_funnel/status/swing_live_dry_run_{date}.status.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (15, 45),
        "window_end": (16, 5),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_selection_funnel_report",
        "path_template": "data/report/swing_selection_funnel/swing_selection_funnel_{date}.md",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (15, 45),
        "window_end": (16, 5),
    },
    {
        "id": "swing_lifecycle_audit_report",
        "path_template": "data/report/swing_lifecycle_audit/swing_lifecycle_audit_{date}.md",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (15, 45),
        "window_end": (16, 5),
    },
    {
        "id": "swing_threshold_ai_review_report",
        "path_template": "data/report/swing_threshold_ai_review/swing_threshold_ai_review_{date}.md",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (15, 45),
        "window_end": (16, 5),
    },
    {
        "id": "swing_improvement_automation_report",
        "path_template": "data/report/swing_improvement_automation/swing_improvement_automation_{date}.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (15, 45),
        "window_end": (16, 5),
    },
    {
        "id": "swing_runtime_approval_report",
        "path_template": "data/report/swing_runtime_approval/swing_runtime_approval_{date}.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (15, 45),
        "window_end": (16, 5),
    },
    {
        "id": "scalping_pattern_lab_automation_report",
        "path_template": "data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
    },
    {
        "id": "swing_pattern_lab_automation_report",
        "path_template": "data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
    },
    {
        "id": "swing_model_retrain_diagnosis",
        "path_template": "data/report/swing_model_retrain/diagnosis_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_bull_period_ai_review",
        "path_template": "data/report/swing_model_retrain/bull_period_ai_review_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_model_retrain_report",
        "path_template": "data/report/swing_model_retrain/swing_model_retrain_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_model_retrain_status",
        "path_template": "data/report/swing_model_retrain/status/swing_model_retrain_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_model_registry_current",
        "path_template": "data/model_registry/swing_v2/current.json",
        "max_staleness_sec": 7776000,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_daily_simulation_status",
        "path_template": "data/report/swing_daily_simulation/status/swing_daily_simulation_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (21, 0),
        "window_end": (21, 50),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_daily_simulation_report",
        "path_template": "data/report/swing_daily_simulation/swing_daily_simulation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (21, 0),
        "window_end": (21, 50),
    },
    {
        "id": "update_kospi_status",
        "path_template": "data/runtime/update_kospi_status/update_kospi_{date}.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": False,
        "window_start": (21, 0),
        "window_end": (21, 30),
        "json_status_field": "status",
        "json_ok_values": ["completed", "skipped_non_trading_day"],
    },
]


@register_detector
class ArtifactFreshnessDetector(BaseDetector):
    id = "artifact_freshness"
    name = "Artifact Freshness Detector"
    category = "artifact"

    def check(self) -> DetectionResult:
        now_dt = datetime.now()
        now_ts = time.time()
        now_h, now_m = _kst_time_tuple(now_dt)
        now_total = now_h * 60 + now_m
        today = _today_kst_str(now_dt)
        trading_day = is_krx_trading_day(now_dt.date())
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
            grace_sec = int(artifact.get("window_grace_sec") or 0)
            if grace_sec > 0 and ws and not past_window_end:
                window_start = now_dt.replace(hour=ws[0], minute=ws[1], second=0, microsecond=0)
                elapsed_from_start = (now_dt - window_start).total_seconds()
                if 0 <= elapsed_from_start <= grace_sec:
                    details[f"{aid}_status"] = "startup_grace"
                    details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                    details[f"{aid}_grace_sec"] = grace_sec
                    continue

            exists = artifact_path.exists()

            if not exists:
                in_progress_cron = self._is_upstream_cron_in_progress(
                    artifact.get("suppress_missing_while_cron_in_progress"),
                    today,
                )
                if in_progress_cron and not past_window_end:
                    warnings.append(f"{aid}: upstream cron in progress; artifact not generated yet")
                    details[f"{aid}_status"] = "warning"
                    details[f"{aid}_upstream_status"] = "in_progress"
                    continue
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
            status_warning = self._validate_json_status(artifact, artifact_path, details)
            if status_warning:
                warnings.append(status_warning)
                details[f"{aid}_status"] = "warning"
                continue

            if artifact.get("one_shot"):
                details[f"{aid}_status"] = "pass_one_shot"
                continue

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

    @staticmethod
    def _is_upstream_cron_in_progress(config: Any, today: str) -> bool:
        if not isinstance(config, dict):
            return False
        log_value = str(config.get("log") or "").strip()
        if not log_value:
            return False
        log_path = PROJECT_ROOT / log_value
        if not log_path.exists():
            return False
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]
        except OSError:
            return False
        today_lines = [line for line in lines if today in line or f"target_date={today}" in line]
        if not today_lines:
            return False
        has_start = any("[START]" in line or "[BEGIN]" in line for line in today_lines)
        has_done = any("[DONE]" in line or "[OK]" in line or "[SUCCESS]" in line or "[COMPLETED]" in line for line in today_lines)
        has_fail = any("[FAIL]" in line or "[ERROR]" in line or "[CRITICAL]" in line for line in today_lines)
        if not has_start or has_done:
            return False
        if has_fail:
            return False
        return True

    @staticmethod
    def _validate_json_status(
        artifact: dict[str, Any],
        artifact_path: Path,
        details: dict[str, Any],
    ) -> str:
        status_field = artifact.get("json_status_field")
        if not status_field:
            return ""

        aid = artifact["id"]
        ok_values = {str(v) for v in artifact.get("json_ok_values", [])}
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except Exception as exc:
            details[f"{aid}_content_status"] = "invalid_json"
            return f"{aid}: invalid status JSON ({exc})"

        current: Any = payload
        for part in str(status_field).split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                details[f"{aid}_content_status"] = "missing_status_field"
                return f"{aid}: missing JSON status field {status_field}"

        status_value = str(current)
        details[f"{aid}_content_status"] = status_value
        if ok_values and status_value not in ok_values:
            return f"{aid}: JSON status is {status_value}"
        return ""


def _kst_time_tuple(now_kst: datetime | None = None) -> tuple[int, int]:
    now_kst = now_kst or datetime.now()
    return now_kst.hour, now_kst.minute
