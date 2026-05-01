from types import SimpleNamespace
from datetime import time as dt_time

from src.engine import sniper_overnight_gatekeeper as overnight
from src.engine import sniper_state_handlers as handlers


class DummyFlowAI:
    def __init__(self, action):
        self.action = action
        self.calls = []

    def evaluate_scalping_holding_flow(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {
            "action": self.action,
            "score": 18 if self.action == "HOLD" else 82,
            "flow_state": "흡수" if self.action == "HOLD" else "붕괴",
            "thesis": "flow thesis",
            "evidence": ["tick flow", "minute flow"],
            "reason": f"flow {self.action}",
            "next_review_sec": 45,
            "ai_parse_fail": False,
        }


def _patch_holding_context(monkeypatch, logs):
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda token, code, limit=30: [{"price": 10000, "volume": 10, "side": "BUY"}],
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda token, code, limit=60: [
            {"close": 9950, "high": 10050, "low": 9900, "volume": 1000},
            {"close": 10000, "high": 10080, "low": 9940, "volume": 1200},
        ],
    )
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        handlers,
        "_emit_stat_action_decision_snapshot",
        lambda **kwargs: logs.append(("stat_action_decision_snapshot", kwargs)),
    )


def _stock():
    return {"name": "테스트", "strategy": "SCALPING", "buy_qty": 1}


def _ws():
    return {
        "curr": 10000,
        "v_pw": 120,
        "buy_ratio": 58,
        "orderbook": {"asks": [{"price": 10010}], "bids": [{"price": 9990}]},
    }


def test_soft_stop_candidate_with_flow_hold_defers_sell(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("HOLD")

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-1.10,
        peak_profit=0.00,
        drawdown=1.10,
        current_ai_score=25,
        held_sec=80,
        curr_price=10000,
        buy_price=10110,
        now_ts=1000.0,
    )

    assert proceed is False
    assert len(ai.calls) == 1
    assert any(stage == "holding_flow_override_defer_exit" for stage, _ in logs)


def test_bad_entry_candidate_with_flow_exit_allows_sell(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("EXIT")

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_bad_entry_refined_canary",
        sell_reason_type="LOSS",
        reason="bad entry",
        profit_rate=-1.30,
        peak_profit=0.00,
        drawdown=1.30,
        current_ai_score=30,
        held_sec=190,
        curr_price=10000,
        buy_price=10130,
        now_ts=1000.0,
    )

    assert proceed is True
    assert len(ai.calls) == 1
    assert any(stage == "holding_flow_override_exit_confirmed" for stage, _ in logs)


def test_low_score_flow_hold_is_not_cut_by_score_band(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("HOLD")

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_ai_momentum_decay",
        sell_reason_type="MOMENTUM_DECAY",
        reason="low score momentum decay",
        profit_rate=0.70,
        peak_profit=1.40,
        drawdown=0.70,
        current_ai_score=18,
        held_sec=140,
        curr_price=10070,
        buy_price=10000,
        now_ts=1000.0,
    )

    assert proceed is False
    assert any(fields.get("flow_score") == 18 for stage, fields in logs if stage == "holding_flow_override_defer_exit")


def test_worsen_floor_stops_defer_and_allows_original_exit(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("HOLD")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": 990.0,
        "holding_flow_override_candidate_profit": 0.00,
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-0.81,
        peak_profit=0.00,
        drawdown=0.81,
        current_ai_score=30,
        held_sec=100,
        curr_price=9919,
        buy_price=10000,
        now_ts=1000.0,
    )

    assert proceed is True
    assert ai.calls == []
    assert any(
        stage == "holding_flow_override_force_exit" and fields.get("force_reason") == "worsen_floor"
        for stage, fields in logs
    )


def test_hard_stop_is_outside_holding_flow_override_scope():
    assert handlers._holding_flow_override_applicable("SCALPING", "scalp_hard_stop_pct") is False


def test_overnight_sell_today_flow_hold_flips_to_hold_overnight(monkeypatch):
    logs = []
    monkeypatch.setattr(
        overnight.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda token, code, limit=30: [{"price": 10000, "volume": 10, "side": "BUY"}],
    )
    monkeypatch.setattr(
        overnight.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda token, code, limit=60: [{"close": 10000, "high": 10050, "low": 9950, "volume": 1000}],
    )
    monkeypatch.setattr(
        overnight,
        "_log_holding_pipeline",
        lambda name, code, stage, **fields: logs.append((stage, fields)),
    )
    ai = DummyFlowAI("HOLD")
    record = SimpleNamespace(
        id=1,
        stock_code="005930",
        stock_name="삼성전자",
        status="HOLDING",
        buy_qty=1,
        buy_price=10000,
    )
    mem_stock = {"name": "삼성전자", "buy_qty": 1}

    decision = overnight._apply_overnight_flow_override(
        record,
        mem_stock,
        {"curr": 10000, "v_pw": 130, "buy_ratio": 60},
        {"avg_price": 10000, "curr_price": 10000, "pnl_pct": 0.0, "score": 45},
        {"action": "SELL_TODAY", "confidence": 35, "reason": "overnight sell"},
        ai,
    )

    assert decision["action"] == "HOLD_OVERNIGHT"
    assert mem_stock["overnight_flow_override_hold"] is True
    assert mem_stock["overnight_flow_override_candidate_profit"] == 0.0
    assert any(stage == "overnight_flow_override_hold" for stage, _ in logs)


def test_overnight_flow_hold_reverts_between_1520_and_1530_on_worsen_floor():
    stock = {
        "overnight_flow_override_hold": True,
        "overnight_flow_override_candidate_profit": 0.10,
        "overnight_flow_override_worsen_pct": 0.80,
    }

    assert handlers._should_revert_overnight_flow_override_hold(stock, -0.70, dt_time(15, 25)) is True
    assert handlers._should_revert_overnight_flow_override_hold(stock, -0.69, dt_time(15, 25)) is False
    assert handlers._should_revert_overnight_flow_override_hold(stock, -0.80, dt_time(15, 30)) is False
