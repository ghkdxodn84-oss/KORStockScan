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
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "calibration_state": "adjust_up",
                        "safety_revert_required": False,
                    }
                ],
                "threshold_snapshot": {"bad_entry_block": {"apply_ready": True}},
                "post_apply_attribution": {"status": "pending_applied_cohort"},
                "safety_guard_pack": [{"family": "soft_stop_whipsaw_confirmation"}],
                "calibration_trigger_pack": [{"family": "soft_stop_whipsaw_confirmation"}],
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
    assert manifest["calibration_candidates"][0]["family"] == "soft_stop_whipsaw_confirmation"
    assert manifest["calibration_policy"]["condition_miss_action"] == "calibration_trigger"
    saved = json.loads((apply_dir / "threshold_apply_2026-05-04.json").read_text(encoding="utf-8"))
    assert saved["source_date"] == "2026-04-30"


def test_build_preopen_apply_manifest_accepts_calibrated_apply_candidate(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)

    (report_dir / "threshold_cycle_2026-05-07.json").write_text(
        json.dumps(
            {
                "date": "2026-05-07",
                "apply_candidate_list": [],
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "apply_mode": "calibrated_apply_candidate",
                        "safety_revert_required": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-08",
        source_date="2026-05-07",
        apply_mode="calibrated_apply_candidate",
    )

    assert manifest["status"] == "calibrated_manifest_ready"
    assert manifest["runtime_change"] is False
    assert manifest["calibration_candidates"][0]["apply_mode"] == "calibrated_apply_candidate"
    assert manifest["calibration_policy"]["rollback_policy"] == "safety_breach_only"


def test_build_preopen_apply_manifest_accepts_efficient_tradeoff_candidate(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-07.json").write_text(
        json.dumps(
            {
                "date": "2026-05-07",
                "apply_candidate_list": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "apply_mode": "efficient_tradeoff_canary_candidate",
                    }
                ],
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "apply_mode": "efficient_tradeoff_canary_candidate",
                        "calibration_state": "adjust_up",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-08",
        source_date="2026-05-07",
        apply_mode="efficient_tradeoff_canary_candidate",
    )

    assert manifest["status"] == "efficient_tradeoff_manifest_ready"
    assert manifest["runtime_change"] is False
    assert manifest["candidates"][0]["family"] == "score65_74_recovery_probe"
    assert manifest["calibration_policy"]["sample_shortfall_action"] == "cap_reduce_or_hold_sample_or_max_step_shrink"


def test_auto_bounded_live_writes_runtime_env_with_ai_guard_and_stage_priority(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "apply_candidate_list": [],
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding_exit",
                        "priority": 1,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED",
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC",
                        ],
                        "recommended_values": {"enabled": True, "confirm_sec": 45},
                        "threshold_version": "soft_stop_whipsaw_confirmation:test",
                    },
                    {
                        "family": "bad_entry_refined_canary",
                        "stage": "holding_exit",
                        "priority": 20,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED"],
                        "recommended_values": {"enabled": True},
                    },
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
                            "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE",
                        ],
                        "recommended_values": {"enabled": True, "min_buy_pressure": 65.0},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "ai_model": "tier2-plus",
                "items": [
                    {"family": "soft_stop_whipsaw_confirmation", "guard_accepted": True, "ai_anomaly_route": "threshold_candidate"},
                    {"family": "bad_entry_refined_canary", "guard_accepted": True, "ai_anomaly_route": "threshold_candidate"},
                    {"family": "score65_74_recovery_probe", "guard_accepted": True, "ai_anomaly_route": "threshold_candidate"},
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["runtime_change"] is True
    selected = {item["family"] for item in manifest["auto_apply_selected"]}
    assert selected == {"soft_stop_whipsaw_confirmation", "score65_74_recovery_probe"}
    blocked = [item for item in manifest["auto_apply_decisions"] if item["family"] == "bad_entry_refined_canary"][0]
    assert blocked["selected"] is False
    assert blocked["decision_reason"] == "same_stage_owner_conflict:soft_stop_whipsaw_confirmation"
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC=45" in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65" in env_text


def test_auto_bounded_live_excludes_ai_instrumentation_gap(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "score65_74_recovery_probe",
                        "guard_accepted": True,
                        "ai_anomaly_route": "instrumentation_gap",
                        "route_action": "exclude_from_threshold_candidate_review",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_blocked"
    assert manifest["runtime_change"] is False
    assert manifest["runtime_env_file"] is None
    assert manifest["auto_apply_decisions"][0]["decision_reason"] == "ai_route_excluded_from_threshold_candidate"
    assert not runtime_dir.exists()


def test_swing_approval_required_request_does_not_auto_apply_without_artifact(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    report_dir.mkdir(parents=True)
    swing_request_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0",
                    "real_order_allowed_actions": ["BUY_INITIAL", "SELL_CLOSE"],
                    "sim_only_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                    "blocked_real_order_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                },
                "approval_requests": [
                    {
                        "approval_id": "swing_runtime_approval:2026-05-08:swing_model_floor",
                        "family": "swing_model_floor",
                        "stage": "selection",
                        "target_env_keys": ["SWING_FLOOR_BULL"],
                        "current_values": {"floor_bull": 0.35},
                        "recommended_values": {"floor_bull": 0.30},
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["swing_runtime_approval"]["requested"] == 1
    assert manifest["swing_runtime_approval"]["approved"] == 0
    assert "approval_artifact_missing" in manifest["swing_runtime_approval"]["blocked"]
    assert not runtime_dir.exists()


def test_swing_user_approval_artifact_applies_env_and_keeps_dry_run(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_runtime_approval:2026-05-08:swing_model_floor"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0",
                    "real_order_allowed_actions": ["BUY_INITIAL", "SELL_CLOSE"],
                    "sim_only_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                    "blocked_real_order_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "family": "swing_model_floor",
                        "stage": "selection",
                        "target_env_keys": ["SWING_FLOOR_BULL", "SWING_FLOOR_BEAR"],
                        "current_values": {"floor_bull": 0.35, "floor_bear": 0.40},
                        "recommended_values": {"floor_bull": 0.30, "floor_bear": 0.35},
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "swing_runtime_approvals_2026-05-08.json").write_text(
        json.dumps({"approved_requests": [{"approval_id": approval_id, "approved": True}]}),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is True
    assert manifest["swing_runtime_approval"]["approved"] == 1
    assert (
        manifest["swing_runtime_approval"]["real_canary_policy"]["policy_id"]
        == "swing_one_share_real_canary_phase0"
    )
    assert manifest["swing_runtime_approval"]["real_canary_policy"]["sim_only_actions"] == [
        "AVG_DOWN",
        "PYRAMID",
        "SCALE_IN",
    ]
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_FLOOR_BULL"] == "0.3"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"] == "true"
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SWING_FLOOR_BULL=0.3" in env_text
    assert "KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true" in env_text


def test_build_preopen_apply_manifest_reports_missing_source(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", tmp_path / "apply_plans")

    manifest = mod.build_preopen_apply_manifest("2026-05-04")

    assert manifest["status"] == "missing_source_report"
    assert manifest["runtime_change"] is False
    assert manifest["candidates"] == []
    assert manifest["calibration_candidates"] == []
