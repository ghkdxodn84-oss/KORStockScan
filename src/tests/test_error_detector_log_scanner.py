from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.engine.error_detectors.log_scanner import LogScanner, SCAN_STATE_PATH


class TestLogScanner:
    def setup_method(self):
        if SCAN_STATE_PATH.exists():
            SCAN_STATE_PATH.unlink()

    def teardown_method(self):
        if SCAN_STATE_PATH.exists():
            SCAN_STATE_PATH.unlink()

    def test_pass_when_no_log_files(self):
        scanner = LogScanner()
        with _mock_logs_dir(tempfile.mkdtemp()):
            result = scanner.check()
        assert result.severity == "pass"

    def test_pass_when_no_new_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "test_error.log"
            log_file.write_text("normal line\n[DONE] ok\n", encoding="utf-8")
            with _mock_logs_dir(log_dir):
                scanner = LogScanner()
                result = scanner.check()
        assert result.severity == "pass"

    def test_warning_on_few_new_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "test_error.log"
            log_file.write_text(
                "[ERROR] something failed\n[WARN] connection timeout\n", encoding="utf-8"
            )
            with _mock_logs_dir(log_dir):
                scanner = LogScanner()
                result = scanner.check()
        assert result.severity in ("warning", "fail")

    def test_fail_on_error_burst(self):
        scanner = LogScanner()
        with _mock_logs_dir(None):
            pass
        result = scanner._classify(
            10,
            __import__("collections").Counter({"API_ERROR": 6, "DB_ERROR": 4}),
        )
        severity, _ = result
        assert severity == "fail"

    def test_state_file_tracking(self):
        scanner = LogScanner()
        state = scanner._load_state()
        assert state == {}

        scanner._save_state({"test_file.log": {"position": 100, "scanned_at": 12345.0}})
        assert SCAN_STATE_PATH.exists()

        loaded = scanner._load_state()
        assert loaded["test_file.log"]["position"] == 100

    def test_scan_file_only_new_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text("old ok line\n", encoding="utf-8")
            initial_size = log_file.stat().st_size
            log_file.write_text(
                log_file.read_text(encoding="utf-8") + "[ERROR] new failure\n",
                encoding="utf-8",
            )

            scanner = LogScanner()
            errors, new_pos, details = scanner._scan_file(
                log_file, initial_size, __import__("collections").Counter()
            )
            assert errors == 1
            assert new_pos > initial_size

    def test_scan_file_no_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text("no error here\n", encoding="utf-8")
            scanner = LogScanner()
            errors, new_pos, details = scanner._scan_file(
                log_file, log_file.stat().st_size, __import__("collections").Counter()
            )
            assert errors == 0

    def test_dry_run_does_not_save_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "test_error.log"
            log_file.write_text("[ERROR] new error\n", encoding="utf-8")
            with _mock_logs_dir(log_dir):
                scanner = LogScanner(dry_run=True)
                result = scanner.check()
                assert result.severity in ("warning", "fail")
                assert not SCAN_STATE_PATH.exists()

    def test_scan_file_rotation_reset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text("[ERROR] old log contents\n", encoding="utf-8")
            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors1, pos1, _ = scanner._scan_file(log_file, 0, counter)
            assert errors1 == 1
            log_file.write_text("[ERROR] new after rotation\n", encoding="utf-8")
            stale_pos = pos1 + 9999
            errors2, pos2, _ = scanner._scan_file(log_file, stale_pos, counter)
            assert errors2 == 1
            assert pos2 > 0


@contextmanager
def _mock_logs_dir(tmpdir_path):
    import src.engine.error_detectors.log_scanner as ls
    orig = ls.LOGS_DIR

    if tmpdir_path is not None:
        ls.LOGS_DIR = Path(tmpdir_path)
    else:
        ls.LOGS_DIR = Path("/nonexistent_logs_xxx")
    try:
        yield
    finally:
        ls.LOGS_DIR = orig
