from dataclasses import replace
from datetime import datetime

import src.engine.sniper_execution_receipts as receipts
import src.engine.sniper_s15_fast_track as s15
import src.engine.sniper_sync as sniper_sync
import src.engine.sniper_state_handlers as state_handlers
from src.engine.trade_profit import calculate_net_profit_rate
from src.utils.constants import TRADING_RULES as CONFIG


class _Bus:
    def __init__(self):
        self.events = []

    def publish(self, topic, payload):
        self.events.append((topic, payload))


class _ReceiptSession:
    def __init__(self, record):
        self.record = record

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.record


class _ReceiptDB:
    def __init__(self, record):
        self.record = record

    def get_session(self):
        return _ReceiptSession(self.record)


class _SyncSession:
    def __init__(self, active_records, pending_records):
        self._active_records = active_records
        self._pending_records = pending_records
        self._mode = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        self._mode = None
        return self

    def filter(self, *args, **kwargs):
        self._mode = "active"
        return self

    def filter_by(self, **kwargs):
        self._mode = kwargs.get("status")
        return self

    def all(self):
        if self._mode == "BUY_ORDERED":
            return list(self._pending_records)
        return list(self._active_records)


class _SyncDB:
    def __init__(self, active_records, pending_records=None):
        self._session = _SyncSession(active_records, pending_records or [])

    def get_session(self):
        return self._session

    def get_latest_is_nxt(self, code):
        return False


class _S15Session:
    def __init__(self, record=None):
        self.record = record
        self.added = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.record

    def add(self, record):
        self.record = record
        self.added = record


class _S15DB:
    def __init__(self, session):
        self._session = session

    def get_session(self):
        return self._session


class _DummyLock:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


class _StateQuery:
    def __init__(self, record):
        self.record = record

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.record

    def update(self, values):
        if self.record is not None:
            for key, value in values.items():
                setattr(self.record, key, value)
        return 1


class _StateSession:
    def __init__(self, record):
        self.record = record

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return _StateQuery(self.record)


class _StateDB:
    def __init__(self, record):
        self.record = record

    def get_session(self):
        return _StateSession(self.record)


def test_trade_profit_helper_accounts_for_costs():
    assert calculate_net_profit_rate(100000, 100100) == -0.13
    assert calculate_net_profit_rate(14320, 14420) == 0.47


def test_sell_receipt_persists_net_profit_rate(monkeypatch):
    record = type(
        "Record",
        (),
        {"buy_price": 100000.0, "status": "SELL_ORDERED", "sell_price": 0, "sell_time": None, "profit_rate": 0.0},
    )()

    receipts.DB = _ReceiptDB(record)
    receipts.event_bus = _Bus()
    monkeypatch.setattr(receipts, "_log_holding_pipeline", lambda *args, **kwargs: None)

    receipts._update_db_for_sell(
        7,
        100100,
        datetime(2026, 4, 7, 9, 0, 0),
        {"code": "123456", "name": "TEST", "msg_audience": "ADMIN_ONLY"},
        "SCALPING",
        False,
    )

    assert record.status == "COMPLETED"
    assert record.sell_price == 100100
    assert record.profit_rate == -0.13
    assert receipts.event_bus.events
    _, payload = receipts.event_bus.events[-1]
    assert "-0.13%" in payload["message"]


def test_periodic_account_sync_uses_net_profit_rate_for_missing_sell_receipt(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "stock_code": "123456",
            "stock_name": "TEST",
            "status": "SELL_ORDERED",
            "buy_price": 100000.0,
            "buy_qty": 1,
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [{"code": "123456", "status": "SELL_ORDERED", "sell_target_price": 100100}]
    sniper_sync.HIGHEST_PRICES = {"123456": 100500}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(sniper_sync.kiwoom_utils, "get_account_balance_kt00005", lambda token: ([], {"KRX"}))

    sniper_sync.periodic_account_sync()

    assert record.status == "COMPLETED"
    assert record.sell_price == 100100
    assert record.profit_rate == -0.13
    assert sniper_sync.ACTIVE_TARGETS[0]["status"] == "COMPLETED"
    assert "123456" not in sniper_sync.HIGHEST_PRICES


def test_s15_candidate_does_not_store_expiry_in_profit_rate():
    session = _S15Session()
    s15.DB = _S15DB(session)

    s15._save_armed_candidate_to_db("123456", "TEST", "COND", 100.0, 160.0)

    assert session.added is not None
    assert session.added.profit_rate == 0.0
    assert session.added.hard_stop_price == 160.0
    assert session.added.nxt == 100.0


def test_holding_state_uses_net_profit_rate_for_sell_decision(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        STOP_LOSS_BULL=0.0,
        STOP_LOSS_BEAR=0.0,
        HOLDING_DAYS=99,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
    )
    state_handlers.KIWOOM_TOKEN = "token"
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}

    record = type("Record", (), {"buy_qty": 1, "status": "HOLDING"})()
    state_handlers.DB = _StateDB(record)

    sell_calls = []
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 100000,
        "buy_qty": 1,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 100100},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert sell_calls
    assert stock["status"] == "SELL_ORDERED"
    assert "-0.13%" in stock["pending_sell_msg"]
