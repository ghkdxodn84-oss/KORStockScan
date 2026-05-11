from src.engine.runtime_ai_router import RuntimeAIEngineRouter, resolve_scalping_ai_route


class _Engine:
    def __init__(self, name):
        self.name = name

    def analyze_target(self, *args, **kwargs):
        return {"engine": self.name}

    def _extract_scalping_features(self, *args, **kwargs):
        return {"engine": self.name}


def test_scalping_route_defaults_to_openai(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_AI_ROUTE", raising=False)
    assert resolve_scalping_ai_route() == "openai"


def test_scalping_route_accepts_deepseek(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_AI_ROUTE", "deepseek")
    assert resolve_scalping_ai_route() == "deepseek"


def test_router_uses_openai_by_default_when_engine_exists():
    router = RuntimeAIEngineRouter(
        gemini_engine=_Engine("gemini"),
        openai_scalping_engine=_Engine("openai"),
        runtime_role="main",
        scalping_ai_route=resolve_scalping_ai_route(),
    )
    assert router.analyze_target("x", {}, [], [])["engine"] == "openai"
    assert router._extract_scalping_features()["engine"] == "openai"


def test_router_uses_openai_only_when_explicitly_selected():
    router = RuntimeAIEngineRouter(
        gemini_engine=_Engine("gemini"),
        openai_scalping_engine=_Engine("openai"),
        runtime_role="main",
        scalping_ai_route="openai",
    )
    assert router.analyze_target("x", {}, [], [])["engine"] == "openai"
    assert router._extract_scalping_features()["engine"] == "openai"


def test_router_uses_deepseek_only_when_explicitly_selected():
    router = RuntimeAIEngineRouter(
        gemini_engine=_Engine("gemini"),
        deepseek_scalping_engine=_Engine("deepseek"),
        runtime_role="main",
        scalping_ai_route="deepseek",
    )
    assert router.analyze_target("x", {}, [], [])["engine"] == "deepseek"
    assert router._extract_scalping_features()["engine"] == "deepseek"


def test_router_keeps_openai_on_holding_profile_when_selected():
    router = RuntimeAIEngineRouter(
        gemini_engine=_Engine("gemini"),
        openai_scalping_engine=_Engine("openai"),
        runtime_role="main",
        scalping_ai_route="openai",
    )
    assert router.analyze_target("x", {}, [], [], prompt_profile="holding")["engine"] == "openai"


def test_router_keeps_deepseek_on_holding_profile_when_selected():
    router = RuntimeAIEngineRouter(
        gemini_engine=_Engine("gemini"),
        deepseek_scalping_engine=_Engine("deepseek"),
        runtime_role="main",
        scalping_ai_route="deepseek",
    )
    assert router.analyze_target("x", {}, [], [], prompt_profile="holding")["engine"] == "deepseek"
