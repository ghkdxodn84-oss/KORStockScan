from src.engine.runtime_ai_router import RuntimeAIEngineRouter, resolve_scalping_ai_route


class _Engine:
    def __init__(self, name):
        self.name = name

    def analyze_target(self, *args, **kwargs):
        return {"engine": self.name}

    def _extract_scalping_features(self, *args, **kwargs):
        return {"engine": self.name}


def test_scalping_route_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_AI_ROUTE", raising=False)
    assert resolve_scalping_ai_route() == "gemini"


def test_router_uses_gemini_by_default_even_with_openai_engine():
    router = RuntimeAIEngineRouter(
        gemini_engine=_Engine("gemini"),
        openai_scalping_engine=_Engine("openai"),
        runtime_role="main",
    )
    assert router.analyze_target("x", {}, [], [])["engine"] == "gemini"
    assert router._extract_scalping_features()["engine"] == "gemini"


def test_router_uses_openai_only_when_explicitly_selected():
    router = RuntimeAIEngineRouter(
        gemini_engine=_Engine("gemini"),
        openai_scalping_engine=_Engine("openai"),
        runtime_role="main",
        scalping_ai_route="openai",
    )
    assert router.analyze_target("x", {}, [], [])["engine"] == "openai"
    assert router._extract_scalping_features()["engine"] == "openai"


def test_router_keeps_holding_profile_on_gemini_even_when_openai_selected():
    router = RuntimeAIEngineRouter(
        gemini_engine=_Engine("gemini"),
        openai_scalping_engine=_Engine("openai"),
        runtime_role="main",
        scalping_ai_route="openai",
    )
    assert router.analyze_target("x", {}, [], [], prompt_profile="holding")["engine"] == "gemini"
