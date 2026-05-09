from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.engine.error_detectors.cron_completion import CronCompletionDetector


class TestCronCompletionDetector:
    def test_pass_when_log_not_yet_due(self):
        detector = CronCompletionDetector()
        with _mock_time(5, 0):
            result = detector.check()
        assert result.severity in ("pass", "warning", "fail")

    def test_pass_when_recent_log_has_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_ok.log"
            log_file.write_text(
                "[START] test job\n[DONE] test job completed successfully\n",
                encoding="utf-8",
            )
            detector = CronCompletionDetector()
            result = detector._read_tail(log_file, 100)
            assert "DONE" in result

    def test_warning_when_log_has_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text(
                "[START] test job\n[FAIL] error occurred\n[ERROR] something broke\n",
                encoding="utf-8",
            )
            detector = CronCompletionDetector()
            result = detector._read_tail(log_file, 100)
            assert "FAIL" in result
            assert "ERROR" in result

    def test_count_errors(self):
        text = "[START] begin\n[ERROR] first\n[FAIL] second\n[DONE] ok"
        detector = CronCompletionDetector()
        assert detector._count_errors(text) == 2

    def test_count_errors_no_match(self):
        detector = CronCompletionDetector()
        assert detector._count_errors("[DONE] all good") == 0

    def test_read_tail_nonexistent(self):
        detector = CronCompletionDetector()
        result = detector._read_tail(Path("/nonexistent/log.log"), 100)
        assert result == ""

    def test_last_terminal_marker_fail_after_done(self):
        detector = CronCompletionDetector()
        lines = "[DONE] target_date=2026-05-09\n[FAIL] target_date=2026-05-09\n"
        assert detector._last_terminal_marker(lines) == "error"

    def test_last_terminal_marker_done_after_fail(self):
        detector = CronCompletionDetector()
        lines = "[FAIL] target_date=2026-05-09\n[DONE] target_date=2026-05-09\n"
        assert detector._last_terminal_marker(lines) == "done"

    def test_last_terminal_marker_none(self):
        detector = CronCompletionDetector()
        lines = "just noise\nno markers\n"
        assert detector._last_terminal_marker(lines) == "none"

    def test_filter_today_lines_excludes_other_dates(self):
        detector = CronCompletionDetector()
        lines = "[DONE] target_date=2026-05-08\n[FAIL] target_date=2026-05-09\n[DONE] target_date=2026-05-09\n"
        filtered = detector._filter_today_lines(lines, "2026-05-09")
        assert "2026-05-08" not in filtered
        assert "[FAIL]" in filtered
        assert filtered.count("[DONE]") == 1


@contextmanager
def _mock_time(hour: int, minute: int):
    import src.engine.error_detectors.cron_completion as cc

    class MockNow:
        def __init__(self):
            self.hour = hour
            self.minute = minute

    class MockDatetime:
        @staticmethod
        def now():
            return MockNow()

    orig = cc.datetime
    cc.datetime = MockDatetime
    try:
        yield
    finally:
        cc.datetime = orig
