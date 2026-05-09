from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.engine.error_detectors.artifact_freshness import (
    ArtifactFreshnessDetector,
    ARTIFACT_REGISTRY,
)


_TRADING_MOCK = "src.engine.error_detectors.artifact_freshness.is_krx_trading_day"


class TestArtifactFreshnessDetector:
    def test_classify_pass(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify([], [])
        assert severity == "pass"

    def test_classify_warning(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify([], ["stale file"])
        assert severity == "warning"

    def test_classify_fail(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify(["missing"], [])
        assert severity == "fail"

    def test_fresh_file_passes(self, tmp_path):
        log_file = tmp_path / "fresh.log"
        log_file.write_text("content", encoding="utf-8")
        artifact = {
            "id": "test_fresh",
            "path_template": str(log_file),
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity in ("pass", "warning", "fail")

    def test_missing_critical_file_fails(self):
        artifact = {
            "id": "test_missing",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "fail"

    def test_window_not_yet_due(self):
        artifact = {
            "id": "test_future",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (23, 59),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            detail_key = "test_future_status"
            assert detail_key in result.details
            assert result.details[detail_key] == "not_yet_due"

    def test_non_trading_day_skips(self):
        artifact = {
            "id": "test_skip",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "trading_day_only": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=False),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("test_skip_status") == "skip_non_trading_day"

    def test_past_window_end_exists_passes(self, tmp_path):
        log_file = tmp_path / "past_window.log"
        log_file.write_text("content", encoding="utf-8")
        artifact = {
            "id": "test_past_window",
            "path_template": str(log_file),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (0, 1),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.details.get("test_past_window_status") == "pass_after_window"

    def test_past_window_end_missing_fails(self):
        artifact = {
            "id": "test_past_window_missing",
            "path_template": "/nonexistent/after_window_file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (0, 1),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "fail"
