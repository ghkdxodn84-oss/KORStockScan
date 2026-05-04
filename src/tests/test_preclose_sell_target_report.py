import json

from src.scanners import preclose_sell_target_report as report_mod


def test_structured_preclose_report_is_report_only_contract():
    payload = report_mod._build_structured_report(
        result={
            "sell_targets": [
                {
                    "rank": 1,
                    "stock_code": "000100",
                    "stock_name": "샘플",
                    "track": "A",
                    "confidence": 71,
                }
            ],
            "summary": "요약",
            "market_caution": "주의",
        },
        report_date="2026-05-04",
        holding_candidates=[{"stock_code": "000100", "score": 64.0}],
        swing_candidates=[{"stock_code": "000200", "composite_score": 0.55}],
        t1_date="2026-05-03",
        use_ai=False,
    )

    assert payload["schema_version"] == report_mod.REPORT_SCHEMA_VERSION
    assert payload["report_type"] == "preclose_sell_target"
    assert payload["automation_stage"] == "R1_daily_report"
    assert payload["policy_status"] == "report_only"
    assert payload["live_runtime_effect"] is False
    assert payload["input_summary"]["track_a_holding_count"] == 1
    assert payload["input_summary"]["track_b_swing_count"] == 1
    assert payload["decision_summary"]["sell_target_count"] == 1
    assert "live_threshold_mutation" in payload["consumer_contract"]["forbidden_use_before_acceptance"]


def test_save_preclose_report_artifacts_writes_canonical_json_and_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "PRE_CLOSE_REPORT_DIR", tmp_path / "preclose_sell_target")
    monkeypatch.setattr(report_mod, "PROJECT_ROOT", tmp_path)
    payload = {
        "schema_version": report_mod.REPORT_SCHEMA_VERSION,
        "report_type": "preclose_sell_target",
        "date": "2026-05-04",
    }

    paths = report_mod._save_report_artifacts(
        "# report\n",
        payload,
        "2026-05-04",
        write_legacy_markdown=True,
    )

    assert paths["json"].exists()
    assert paths["markdown"].exists()
    assert paths["legacy_markdown"].exists()
    assert json.loads(paths["json"].read_text(encoding="utf-8"))["report_type"] == "preclose_sell_target"
    assert paths["markdown"].read_text(encoding="utf-8") == "# report\n"
