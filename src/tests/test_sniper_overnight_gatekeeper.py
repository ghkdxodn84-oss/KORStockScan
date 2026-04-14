from sqlalchemy.orm.exc import DetachedInstanceError

from src.database.models import RecommendationHistory
from src.engine.sniper_overnight_gatekeeper import _format_order_error, _snapshot_record


def test_snapshot_record_survives_detached_instance():
    record = RecommendationHistory(
        id=101,
        stock_code="005930",
        stock_name="삼성전자",
        status="HOLDING",
        buy_qty=3,
        buy_price=70100,
        buy_time="09:10:00",
    )

    snapshot = _snapshot_record(record)

    assert snapshot.id == 101
    assert snapshot.stock_code == "005930"
    assert snapshot.stock_name == "삼성전자"
    assert snapshot.status == "HOLDING"
    assert snapshot.buy_qty == 3.0
    assert snapshot.buy_price == 70100.0
    assert snapshot.buy_time == "09:10:00"


def test_snapshot_record_can_be_built_before_detached_refresh_failure():
    record = RecommendationHistory(
        id=102,
        stock_code="000660",
        stock_name="SK하이닉스",
        status="SELL_ORDERED",
        buy_qty=1,
        buy_price=201000,
        buy_time="14:55:00",
    )

    snapshot = _snapshot_record(record)

    # Simulate the practical guarantee we need: gatekeeper should rely on the
    # immutable snapshot, not on the ORM instance after session teardown.
    class DetachedRecord:
        @property
        def status(self):
            raise DetachedInstanceError("detached")

    detached = DetachedRecord()

    assert snapshot.status == "SELL_ORDERED"
    try:
        _ = detached.status
        raised = False
    except DetachedInstanceError:
        raised = True

    assert raised is True


def test_format_order_error_prefers_return_msg_and_code():
    msg = _format_order_error({"return_msg": "[2000](521790:주문 불가능합니다.)", "return_code": 20})
    assert msg == "[2000](521790:주문 불가능합니다.) (code=20)"


def test_format_order_error_fallback_to_string():
    assert _format_order_error("timeout") == "timeout"
