import json

from src.engine import threshold_cycle_preopen_apply as mod


def test_build_preopen_apply_manifest_uses_latest_prior_report(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)

    (report_dir / "threshold_cycle_2026-04-29.json").write_text(
        json.dumps({"date": "2026-04-29", "apply_candidate_list": [{"family": "old"}]}),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-04-30.json").write_text(
        json.dumps(
            {
                "date": "2026-04-30",
                "apply_candidate_list": [{"family": "bad_entry_block", "stage": "holding_exit"}],
                "threshold_snapshot": {"bad_entry_block": {"apply_ready": True}},
                "rollback_guard_pack": [{"family": "bad_entry_block"}],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest("2026-05-04")

    assert manifest["status"] == "manifest_ready"
    assert manifest["runtime_change"] is False
    assert manifest["source_date"] == "2026-04-30"
    assert manifest["candidates"] == [{"family": "bad_entry_block", "stage": "holding_exit"}]
    saved = json.loads((apply_dir / "threshold_apply_2026-05-04.json").read_text(encoding="utf-8"))
    assert saved["source_date"] == "2026-04-30"


def test_build_preopen_apply_manifest_reports_missing_source(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", tmp_path / "apply_plans")

    manifest = mod.build_preopen_apply_manifest("2026-05-04")

    assert manifest["status"] == "missing_source_report"
    assert manifest["runtime_change"] is False
    assert manifest["candidates"] == []
