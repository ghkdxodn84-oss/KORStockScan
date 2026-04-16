import os
import socket
from typing import Any

from src.utils.logger import log_info


def resolve_runtime_role() -> str:
    """Return runtime role: main (default) or remote."""
    explicit = str(os.getenv("KORSTOCKSCAN_RUNTIME_ROLE", "") or "").strip().lower()
    if explicit in {"main", "remote"}:
        return explicit

    latency_profile = str(os.getenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", "") or "").strip().lower()
    if "remote" in latency_profile:
        return "remote"

    host = socket.gethostname().strip().lower()
    if any(token in host for token in ("remote", "windy")):
        return "remote"
    return "main"


class RuntimeAIEngineRouter:
    """
    Runtime router:
    - main: scalping analyze_target -> OpenAI engine
    - remote: keep Gemini path (with Gemini's own model routing)
    """

    def __init__(self, *, gemini_engine: Any, openai_scalping_engine: Any = None, runtime_role: str = "main"):
        self.gemini_engine = gemini_engine
        self.openai_scalping_engine = openai_scalping_engine
        self.runtime_role = str(runtime_role or "main").strip().lower()

        openai_enabled = self.runtime_role == "main" and self.openai_scalping_engine is not None
        log_info(
            f"[AI_ROUTER] role={self.runtime_role} "
            f"scalping_openai={'on' if openai_enabled else 'off'}"
        )

    def _is_scalping_strategy(self, strategy: Any) -> bool:
        return str(strategy or "SCALPING").strip().upper() in {"SCALPING", "SCALP"}

    def analyze_target(
        self,
        target_name,
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        program_net_qty=0,
        cache_profile="default",
        prompt_profile="shared",
    ):
        if (
            self.runtime_role == "main"
            and self.openai_scalping_engine is not None
            and self._is_scalping_strategy(strategy)
        ):
            return self.openai_scalping_engine.analyze_target(
                target_name,
                ws_data,
                recent_ticks,
                recent_candles,
                strategy=strategy,
                program_net_qty=program_net_qty,
                cache_profile=cache_profile,
                prompt_profile=prompt_profile,
            )

        return self.gemini_engine.analyze_target(
            target_name,
            ws_data,
            recent_ticks,
            recent_candles,
            strategy=strategy,
            program_net_qty=program_net_qty,
            cache_profile=cache_profile,
            prompt_profile=prompt_profile,
        )

    def generate_realtime_report(self, *args, **kwargs):
        return self.gemini_engine.generate_realtime_report(*args, **kwargs)

    def analyze_target_shadow_prompt(self, *args, **kwargs):
        if hasattr(self.gemini_engine, "analyze_target_shadow_prompt"):
            return self.gemini_engine.analyze_target_shadow_prompt(*args, **kwargs)
        return {"action": "WAIT", "score": 50, "reason": "shadow unsupported"}

    def _extract_scalping_features(self, *args, **kwargs):
        if self.runtime_role == "main" and self.openai_scalping_engine is not None:
            return self.openai_scalping_engine._extract_scalping_features(*args, **kwargs)
        if hasattr(self.gemini_engine, "_extract_scalping_features"):
            return self.gemini_engine._extract_scalping_features(*args, **kwargs)
        return {}

    def __getattr__(self, name: str):
        if hasattr(self.gemini_engine, name):
            return getattr(self.gemini_engine, name)
        if self.openai_scalping_engine is not None and hasattr(self.openai_scalping_engine, name):
            return getattr(self.openai_scalping_engine, name)
        raise AttributeError(name)

