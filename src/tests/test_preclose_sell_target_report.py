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


def test_gemini_preclose_falls_back_to_second_key(monkeypatch):
    class FakeConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeModels:
        def __init__(self, api_key):
            self.api_key = api_key

        def generate_content(self, **kwargs):
            if self.api_key == "key-one":
                raise RuntimeError("quota exhausted")

            class Response:
                text = json.dumps(
                    {
                        "sell_targets": [],
                        "summary": "ok",
                        "market_caution": "none",
                    }
                )

            return Response()

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels(api_key)

    class FakeGenAI:
        Client = FakeClient

    class FakeTypes:
        GenerateContentConfig = FakeConfig

    monkeypatch.setattr(report_mod, "GENAI_AVAILABLE", True)
    monkeypatch.setattr(report_mod, "genai", FakeGenAI)
    monkeypatch.setattr(report_mod, "types", FakeTypes)
    monkeypatch.setattr(
        report_mod,
        "_load_config",
        lambda: {
            "GEMINI_API_KEY": "key-one",
            "GEMINI_API_KEY_2": "key-two",
            "GEMINI_API_KEY_3": "key-three",
        },
    )

    result = report_mod._call_gemini_preclose([], [{"stock_code": "000200"}])

    assert result["summary"] == "ok"
    assert result["ai_provider_status"]["status"] == "success"
    assert result["ai_provider_status"]["key_name"] == "GEMINI_API_KEY_2"
    assert result["ai_provider_status"]["attempted_keys"] == 3
