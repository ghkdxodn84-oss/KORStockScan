from src.engine.approval_contracts import annotate_approval_request, approval_contract_for


def test_approval_contract_registry_marks_ready_swing_contract():
    contract = approval_contract_for("swing_one_share_real_canary_phase0", "2026-05-15")

    assert contract["approval_contract_status"] == "ready"
    assert contract["approval_live_ready"] is True
    assert contract["approval_artifact_path"].endswith("swing_one_share_real_canary_2026-05-15.json")
    assert contract["missing_components"] == []


def test_approval_contract_registry_marks_missing_scalping_manual_contract():
    request = annotate_approval_request({"family": "position_sizing_cap_release"}, "2026-05-15")

    assert request["approval_contract_status"] == "contract_missing"
    assert request["approval_live_ready"] is False
    assert request["approval_artifact_path"].endswith("position_sizing_cap_release_2026-05-15.json")
    assert "approval_artifact_loader" in request["approval_contract_missing_components"]
