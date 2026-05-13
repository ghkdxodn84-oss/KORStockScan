import json

from src.engine import notify_panic_state_transition as mod


def test_panic_sell_start_and_release_notifications(tmp_path, monkeypatch):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin", "user1", "user2"])
    monkeypatch.setattr(mod, "_send_telegram", lambda token, chat_id, message: sent.append((chat_id, message)))

    report.write_text(
        json.dumps(
            {
                "panic_state": "PANIC_SELL",
                "panic_metrics": {"stop_loss_exit_count": 3},
                "microstructure_detector": {"metrics": {"max_panic_score": 0.82}},
            }
        ),
        encoding="utf-8",
    )

    first = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=state,
        now_ts=1000.0,
    )
    second = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=state,
        now_ts=1010.0,
    )
    report.write_text(json.dumps({"panic_state": "NORMAL", "panic_metrics": {}}), encoding="utf-8")
    third = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=state,
        now_ts=1020.0,
    )

    assert first == "sent"
    assert second == "no_transition"
    assert third == "sent"
    assert len(sent) == 6
    assert "패닉셀 주의" in sent[0][1]
    assert "체감 강도: ■■■■■■■■□□ 높음" in sent[0][1]
    assert "패닉셀 경보 해제" in sent[-1][1]
    assert "PANIC_SELL" not in sent[0][1]


def test_panic_buying_test_notice_goes_admin_only(tmp_path, monkeypatch):
    report = tmp_path / "panic_buying.json"
    state = tmp_path / "state.json"
    sent = []
    report.write_text(
        json.dumps(
            {
                "panic_buy_state": "PANIC_BUY",
                "panic_buy_metrics": {"panic_buy_active_count": 2, "max_panic_buy_score": 0.66},
                "exhaustion_metrics": {"exhaustion_candidate_count": 1},
                "tp_counterfactual_summary": {"candidate_context_count": 4},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin", "user1"])
    monkeypatch.setattr(mod, "_send_telegram", lambda token, chat_id, message: sent.append((chat_id, message)))

    status = mod.notify_from_report(
        report,
        kind="panic_buying",
        audience="admin",
        state_file=state,
        force=True,
        now_ts=1000.0,
    )

    assert status == "sent"
    assert [chat_id for chat_id, _ in sent] == ["admin"]
    assert "패닉바잉 주의" in sent[0][1]
    assert "체감 강도: 확인중" not in sent[0][1]
    assert "PANIC_BUY" not in sent[0][1]


def test_missing_config_does_not_send(tmp_path, monkeypatch):
    report = tmp_path / "panic_sell.json"
    report.write_text(json.dumps({"panic_state": "PANIC_SELL"}), encoding="utf-8")
    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("", ""))

    status = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=tmp_path / "state.json",
        now_ts=1000.0,
    )

    assert status == "missing_config"
