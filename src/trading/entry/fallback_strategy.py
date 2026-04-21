from __future__ import annotations

from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_types import PlannedOrder, SignalSnapshot


class FallbackStrategy:
    """Deprecated latency fallback builder.

    The former scout/main bundle submitted two orders without an observe-then-act
    step, which amplified partial/rebase/soft-stop leakage. Keep the class as a
    safe null-object while callers are migrated away from latency fallback.
    """

    def __init__(self, config: EntryConfig) -> None:
        self.config = config

    def build(
        self,
        *,
        snapshot: SignalSnapshot,
        latest_price: int,
        best_ask: int,
    ) -> list[PlannedOrder]:
        return []
