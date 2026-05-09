from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from src.utils.constants import PROJECT_ROOT, TRADING_RULES

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)


HEARTBEAT_PATH = PROJECT_ROOT / "tmp" / "error_detector_heartbeat.json"
_HEARTBEAT_LOCK = threading.Lock()


def write_heartbeat(component: str, alive: bool = True):
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = HEARTBEAT_PATH.with_suffix(HEARTBEAT_PATH.suffix + ".tmp")
    with _HEARTBEAT_LOCK:
        state = {}
        if HEARTBEAT_PATH.exists():
            try:
                state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                state = {}
        now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
        if component == "main_loop":
            state["main_loop"] = {"last_beat": now_iso, "pid": os.getpid()}
        else:
            threads = state.setdefault("threads", {})
            threads[component] = {"last_beat": now_iso, "alive": alive}
        tmp_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, HEARTBEAT_PATH)


@register_detector
class ProcessHealthDetector(BaseDetector):
    id = "process_health"
    name = "Process Health Detector"
    category = "process"

    @property
    def main_loop_timeout_sec(self) -> int:
        return int(getattr(TRADING_RULES, "ERROR_DETECTOR_PROCESS_MAIN_LOOP_TIMEOUT_SEC", 15))

    @property
    def thread_timeout_sec(self) -> int:
        return int(getattr(TRADING_RULES, "ERROR_DETECTOR_PROCESS_THREAD_TIMEOUT_SEC", 7200))

    def check(self) -> DetectionResult:
        now_ts = time.time()
        details: dict = {}
        main_loop_timeout = self.main_loop_timeout_sec
        thread_timeout = self.thread_timeout_sec

        if not HEARTBEAT_PATH.exists():
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="fail",
                summary="Heartbeat file not found. bot_main.py may not be running.",
                details={"heartbeat_path": str(HEARTBEAT_PATH)},
                recommended_action="Check bot_main.py process status and restart if needed.",
            )

        try:
            state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="fail",
                summary=f"Cannot read heartbeat file: {e}",
                details={"heartbeat_path": str(HEARTBEAT_PATH), "error": str(e)},
                recommended_action="Check file permissions and disk health.",
            )

        main_loop = state.get("main_loop")
        thread_issues: list[str] = []
        pid_ok = True

        if main_loop:
            main_beat = _parse_iso(main_loop.get("last_beat", ""))
            main_age = now_ts - main_beat if main_beat else float("inf")
            details["main_loop_age_sec"] = round(main_age, 1)
            details["main_loop_pid"] = main_loop.get("pid")

            pid = main_loop.get("pid")
            if pid:
                pid_alive = _pid_exists(pid)
                details["main_loop_pid_alive"] = pid_alive
                if not pid_alive:
                    pid_ok = False

            if not pid_ok:
                details["main_loop_status"] = "pid_dead"
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="fail",
                    summary=f"bot_main.py PID {pid} is no longer alive. Main process may have died.",
                    details=details,
                    recommended_action="Restart bot_main.py immediately.",
                )
            if main_age > main_loop_timeout:
                details["main_loop_status"] = "stale"
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="fail",
                    summary=f"Main loop heartbeat stale for {main_age:.0f}s (timeout={main_loop_timeout}s).",
                    details=details,
                    recommended_action="Check main loop for deadlock or crash.",
                )
            details["main_loop_status"] = "ok"
        else:
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="fail",
                summary="No main_loop heartbeat entry found.",
                details=details,
                recommended_action="Verify bot_main.py is running with heartbeat instrumentation.",
            )

        threads = state.get("threads", {})
        if not threads:
            details["thread_count"] = 0
            details["thread_status"] = "no_threads"
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="warning",
                summary="No thread heartbeats found. Threads may not have started.",
                details=details,
                recommended_action="Check bot_main.py startup logs for thread launch failures.",
            )

        for tname, tdata in threads.items():
            tbeat = _parse_iso(tdata.get("last_beat", ""))
            tage = now_ts - tbeat if tbeat else float("inf")
            talive = tdata.get("alive", True)
            details.setdefault("thread_age_sec", {})[tname] = round(tage, 1)
            details.setdefault("thread_alive", {})[tname] = talive
            if not talive:
                details.setdefault("stopped_threads", []).append(tname)
            elif tage > thread_timeout:
                thread_issues.append(tname)

        if thread_issues:
            details["stale_threads"] = thread_issues
            details["thread_status"] = "stale"
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="fail",
                summary=f"Stale or dead threads detected: {', '.join(thread_issues)}",
                details=details,
                recommended_action="Investigate thread health. Restart bot_main.py if needed.",
            )

        details["thread_status"] = "ok"
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity="pass",
            summary="All processes and threads healthy.",
            details=details,
        )


def _parse_iso(iso_str: str) -> float | None:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.timestamp()
    except (ValueError, TypeError):
        return None


def _pid_exists(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
