import src.engine.kiwoom_orders as kiwoom_orders
import src.engine.sniper_config as sniper_config


def test_get_deposit_uses_virtual_orderable_amount(monkeypatch):
    monkeypatch.setattr(
        sniper_config,
        "CONF",
        {"VIRTUAL_ORDERABLE_AMOUNT": 10_000_000},
    )
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)

    def _should_not_call_api(*args, **kwargs):
        raise AssertionError("virtual orderable amount is enabled")

    monkeypatch.setattr(kiwoom_orders.requests, "post", _should_not_call_api)

    assert kiwoom_orders.get_deposit("TOKEN") == 10_000_000


def test_get_deposit_falls_back_to_api_when_virtual_amount_disabled(monkeypatch):
    class DummyResponse:
        status_code = 200

        def json(self):
            return {"rt_cd": "0", "ord_alow_amt": "50000000"}

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(
        kiwoom_orders.requests,
        "post",
        lambda *args, **kwargs: DummyResponse(),
    )

    assert kiwoom_orders.get_deposit("TOKEN") == 50_000_000
