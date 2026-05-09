from dataclasses import replace

import pytest

import src.engine.kiwoom_sniper_v2 as sniper_runtime
import src.engine.sniper_performance_tuning_report as perf_report
import src.engine.sniper_state_handlers as state_handlers
from src.engine.daily_threshold_cycle_report import build_daily_threshold_cycle_report
from src.utils.constants import TRADING_RULES as CONFIG
from src.utils.threshold_cycle_registry import threshold_family_for_stage


class FakeEventBus:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload):
        self.published.append((topic, payload))


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SCALP_LIVE_SIMULATOR_ENABLED=True,
        SCALP_LIVE_SIMULATOR_QTY=1,
        SCALP_LIVE_SIMULATOR_ENTRY_TIMEOUT_SEC=90,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {})
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(state_handlers, "LAST_LOG_TIMES", {})
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", tmp_path / "scalp_live_sim_state.json")


def test_scalp_simulator_arms_and_fills_without_real_buy_order(monkeypatch):
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: pytest.fail("real buy order must not be called"),
    )

    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 82.0,
    }
    ws_data = {
        "curr": 9_990,
        "orderbook": {
            "asks": [{"price": 9_990}],
            "bids": [{"price": 9_980}],
        },
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        ws_data,
        runtime,
    )

    assert len(state_handlers.ACTIVE_TARGETS) == 1
    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["status"] == "HOLDING"
    assert sim_target["simulation_book"] == "scalp_ai_buy_all"
    assert sim_target["actual_order_submitted"] is False
    assert sim_target["buy_qty"] == 1
    assert sim_target["buy_price"] == 9_990
    assert [stage for stage, _ in logs] == [
        "scalp_sim_entry_armed",
        "scalp_sim_buy_order_virtual_pending",
        "scalp_sim_buy_order_assumed_filled",
        "scalp_sim_holding_started",
    ]
    assert state_handlers.EVENT_BUS.published == [
        ("COMMAND_WS_REG", {"codes": ["123456"], "source": "scalp_live_simulator"})
    ]


def test_scalp_simulator_duplicate_buy_signal_does_not_create_second_position(monkeypatch):
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    state_handlers.ACTIVE_TARGETS.append(
        {
            "code": "123456",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "simulation_book": "scalp_ai_buy_all",
            "scalp_live_simulator": True,
            "sim_record_id": "SIM-1",
        }
    )

    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 80.0,
    }

    assert not state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 9_990},
        runtime,
    )
    assert len(state_handlers.ACTIVE_TARGETS) == 1
    assert logs[0][0] == "scalp_sim_duplicate_buy_signal"


def test_scalp_simulator_requires_buy_score_threshold():
    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 74.9,
    }

    assert not state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 9_990},
        runtime,
    )
    assert state_handlers.ACTIVE_TARGETS == []


def test_scalp_simulator_preset_tp_sell_does_not_call_real_sell(monkeypatch):
    holding_logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: pytest.fail("real sell order must not be called"),
    )

    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "order_time": 1_000.0,
        "holding_started_at": 1_000.0,
        "exit_mode": "SCALP_PRESET_TP",
        "preset_tp_price": 10_150,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "sim_record_id": "SIM-1",
        "actual_order_submitted": False,
    }

    state_handlers.handle_holding_state(
        stock,
        "123456",
        {
            "curr": 10_150,
            "orderbook": {
                "asks": [{"price": 10_160}],
                "bids": [{"price": 10_140}],
            },
        },
        admin_id=None,
        market_regime="NEUTRAL",
        now_ts=1_060.0,
    )

    assert stock["status"] == "COMPLETED"
    assert stock["sell_price"] == 10_150
    assert stock["actual_order_submitted"] is False
    assert any(stage == "exit_signal" for stage, _ in holding_logs)
    assert any(stage == "scalp_sim_sell_order_assumed_filled" for stage, _ in holding_logs)


def test_scalp_simulator_sell_profit_uses_assumed_fill_price(monkeypatch):
    holding_logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
    )
    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "sim_record_id": "SIM-1",
        "actual_order_submitted": False,
    }

    assert state_handlers._complete_scalp_simulated_sell(
        stock=stock,
        code="123456",
        ws_data={
            "curr": 10_150,
            "orderbook": {
                "asks": [{"price": 10_160}],
                "bids": [{"price": 10_130}],
            },
        },
        curr_price=10_150,
        now_ts=1_060.0,
        sell_reason_type="PROFIT",
        exit_rule="test_exit",
        profit_rate=state_handlers.calculate_net_profit_rate(10_000, 10_150),
    )

    expected_profit = state_handlers.calculate_net_profit_rate(10_000, 10_130)
    assert stock["sell_price"] == 10_130
    assert stock["profit_rate"] == expected_profit
    event = next(fields for stage, fields in holding_logs if stage == "scalp_sim_sell_order_assumed_filled")
    assert event["profit_rate"] == f"{expected_profit:+.2f}"
    assert event["trigger_profit_rate"] == f"{state_handlers.calculate_net_profit_rate(10_000, 10_150):+.2f}"


def test_scalp_simulator_scale_in_does_not_call_real_buy(monkeypatch):
    holding_logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
    )
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: pytest.fail("real add buy order must not be called"),
    )
    monkeypatch.setattr(
        state_handlers,
        "resolve_scale_in_order_price",
        lambda **kwargs: {
            "allowed": True,
            "order_price": 9_990,
            "reason": "test",
            "price_source": "best_bid",
            "best_bid": 9_990,
            "best_ask": 10_000,
            "spread_bps": 10.0,
            "curr_vs_micro_vwap_bp": 0.0,
            "max_spread_bps": 80.0,
            "max_micro_vwap_bps": 60.0,
        },
    )
    monkeypatch.setattr(
        state_handlers,
        "describe_dynamic_scale_in_qty",
        lambda **kwargs: {
            "qty": 1,
            "template_qty": 1,
            "would_qty": 1,
            "effective_qty": 1,
            "cap_qty": 1,
            "floor_applied": False,
            "qty_reason": "test_qty",
        },
    )

    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "sim_record_id": "SIM-1",
        "actual_order_submitted": False,
    }

    res = state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data={
            "curr": 9_990,
            "orderbook": {
                "asks": [{"price": 9_990}],
                "bids": [{"price": 9_980}],
            },
        },
        action={"add_type": "AVG_DOWN", "reason": "test"},
        admin_id=None,
    )

    assert res["simulated_order"] is True
    assert stock["buy_qty"] == 2
    assert stock["actual_order_submitted"] is False
    assert any(stage == "scalp_sim_scale_in_order_assumed_filled" for stage, _ in holding_logs)


def test_scalp_simulator_threshold_stages_are_included():
    assert threshold_family_for_stage("scalp_sim_entry_armed") == "entry_mechanical_momentum"
    assert threshold_family_for_stage("scalp_sim_buy_order_assumed_filled") == "pre_submit_price_guard"
    assert threshold_family_for_stage("scalp_sim_sell_order_assumed_filled") == "statistical_action_weight"


def test_ws_prune_retains_active_scalp_simulator_consumer(monkeypatch):
    class FakeWS:
        subscribed_codes = {"123456"}

    fake_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "WS_MANAGER", FakeWS())
    monkeypatch.setattr(sniper_runtime, "event_bus", fake_bus)
    monkeypatch.setattr(sniper_runtime, "should_retain_ws_subscription", lambda *args, **kwargs: False)

    sniper_runtime._prune_ws_subscriptions_for_inactive_targets(
        [
            {
                "code": "123456",
                "strategy": "SCALPING",
                "status": "SCALP_SIM_PENDING_BUY",
                "simulation_book": "scalp_ai_buy_all",
                "scalp_live_simulator": True,
            }
        ]
    )

    assert fake_bus.published == []


def test_daily_threshold_cycle_report_uses_scalp_sim_completed_rows_as_combined_authority():
    target_date = "2026-05-11"

    def pipeline_loader(day):
        if day != target_date:
            return []
        return [
            {
                "event_type": "pipeline_event",
                "pipeline": "HOLDING_PIPELINE",
                "stage": "scalp_sim_sell_order_assumed_filled",
                "stock_name": "SIM",
                "stock_code": "123456",
                "record_id": None,
                "emitted_date": target_date,
                "fields": {
                    "simulation_book": "scalp_ai_buy_all",
                    "sim_record_id": "SIM-1",
                    "profit_rate": "+0.50",
                    "qty": "1",
                    "buy_price": "10000",
                    "assumed_fill_price": "10050",
                    "actual_order_submitted": "False",
                },
            }
        ]

    def completed_rows_loader(start_date, end_date):
        return [
            {
                "rec_date": target_date,
                "stock_code": "000001",
                "stock_name": "REAL",
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "profit_rate": 0.2,
                "add_count": 0,
                "avg_down_count": 0,
                "pyramid_count": 0,
            }
        ]

    report = build_daily_threshold_cycle_report(
        target_date,
        pipeline_loader=pipeline_loader,
        report_source_loader=lambda _: {},
        completed_rows_loader=completed_rows_loader,
    )

    assert report["summary"]["real_completed_valid_rolling_7d"] == 1
    assert report["summary"]["sim_completed_valid_rolling_7d"] == 1
    assert report["summary"]["completed_valid_rolling_7d"] == 2
    assert report["completed_by_source"]["combined"]["sample"] == 2
    assert report["completed_by_source"]["sim"]["sample"] == 1
    assert report["scalp_simulator"]["sell_completed"] == 1


def test_performance_tuning_source_split_combines_real_and_scalp_sim():
    split = perf_report._build_completed_source_split(
        [
            {
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "profit_rate": 0.2,
            }
        ],
        [
            perf_report.PerfEvent(
                timestamp="2026-05-11T10:00:00",
                name="SIM",
                code="123456",
                stage="scalp_sim_sell_order_assumed_filled",
                fields={"profit_rate": "+0.50", "simulation_book": "scalp_ai_buy_all"},
                raw_line="",
            )
        ],
    )

    assert split["real"]["completed_rows"] == 1
    assert split["sim"]["completed_rows"] == 1
    assert split["combined"]["completed_rows"] == 2
    assert split["combined"]["avg_profit_rate"] == 0.35
    assert split["calibration_authority"] == "combined_equal_weight_no_sim_downweight"
