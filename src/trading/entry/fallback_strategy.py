from __future__ import annotations

from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_types import PlannedOrder, SignalSnapshot
from src.trading.order.order_types import OrderType, TimeInForce
from src.trading.order.tick_utils import move_price_by_ticks


class FallbackStrategy:
    """Builds scout-plus-main defensive orders for CAUTION mode only."""

    def __init__(self, config: EntryConfig) -> None:
        self.config = config

    def build(
        self,
        *,
        snapshot: SignalSnapshot,
        latest_price: int,
        best_ask: int,
    ) -> list[PlannedOrder]:
        scout_qty = self._compute_scout_qty(snapshot.planned_qty)
        main_qty = max(0, snapshot.planned_qty - scout_qty)
        tif_scout = (
            TimeInForce.IOC.value
            if self.config.enable_ioc_for_fallback_scout
            else TimeInForce.DAY.value
        )
        tif_main = (
            TimeInForce.IOC.value
            if self.config.enable_ioc_for_fallback_main
            else TimeInForce.DAY.value
        )

        aggressive_anchor = best_ask if best_ask > 0 else latest_price
        scout_price = move_price_by_ticks(
            aggressive_anchor,
            self.config.fallback_scout_aggressive_ticks,
        )
        main_anchor = min(snapshot.signal_price, latest_price) if latest_price > 0 else snapshot.signal_price
        main_price = move_price_by_ticks(main_anchor, -self.config.fallback_main_defensive_ticks)

        orders = [
            PlannedOrder(
                symbol=snapshot.symbol,
                side=snapshot.side,
                qty=scout_qty,
                price=scout_price,
                order_type=OrderType.LIMIT.value,
                tif=tif_scout,
                tag="fallback_scout",
            )
        ]
        if main_qty > 0:
            orders.append(
                PlannedOrder(
                    symbol=snapshot.symbol,
                    side=snapshot.side,
                    qty=main_qty,
                    price=main_price,
                    order_type=OrderType.LIMIT.value,
                    tif=tif_main,
                    tag="fallback_main",
                )
            )
        return orders

    def _compute_scout_qty(self, planned_qty: int) -> int:
        mode = str(self.config.scout_qty_mode).upper()
        if mode == "PERCENT":
            qty = max(int(planned_qty * self.config.scout_qty_percent), self.config.scout_min_qty)
            return min(max(1, qty), planned_qty)
        return min(max(1, self.config.scout_min_qty), planned_qty)
