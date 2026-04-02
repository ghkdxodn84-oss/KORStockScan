from __future__ import annotations

from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_types import PlannedOrder, SignalSnapshot
from src.trading.order.order_types import OrderType, TimeInForce
from src.trading.order.tick_utils import move_price_by_ticks


class NormalEntryBuilder:
    """Builds a single defensive normal-mode order under SAFE conditions."""

    def __init__(self, config: EntryConfig) -> None:
        self.config = config

    def build(self, *, snapshot: SignalSnapshot, latest_price: int) -> PlannedOrder:
        tif = TimeInForce.IOC.value if self.config.enable_ioc_for_normal else TimeInForce.DAY.value
        defensive_price = move_price_by_ticks(latest_price, -self.config.normal_defensive_ticks)
        return PlannedOrder(
            symbol=snapshot.symbol,
            side=snapshot.side,
            qty=snapshot.planned_qty,
            price=defensive_price,
            order_type=OrderType.LIMIT.value,
            tif=tif,
            tag="normal",
        )
