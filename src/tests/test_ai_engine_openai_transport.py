import threading
from dataclasses import replace
from types import SimpleNamespace

from src.engine import ai_engine_openai as openai_module
from src.engine.ai_engine_openai import (
    GPTSniperEngine,
    OPENAI_RESPONSE_SCHEMA_REGISTRY,
    OpenAIResponseRequest,
    OpenAIResponsesWSPool,
    OpenAITransportResult,
    OpenAIWSRequestIdMismatchError,
)


def _build_engine():
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    engine.api_call_lock = threading.Lock()
    engine.current_model_name = "gpt-fast"
    engine.model_tier1_fast = "gpt-fast"
    engine.model_tier2_balanced = "gpt-report"
    engine.model_tier3_deep = "gpt-deep"
    engine.fast_model_name = "gpt-fast"
    engine.report_model_name = "gpt-report"
    engine.deep_model_name = "gpt-deep"
    engine.api_keys = ["key-a", "key-b"]
    engine.current_key = "key-a"
    engine.current_api_key_index = 0
    engine._rotate_client = lambda: None
    engine._transport_local = threading.local()
    engine._ws_metrics_lock = threading.Lock()
    engine._ws_metrics = {
        "openai_ws_requests": 0,
        "openai_ws_completed": 0,
        "openai_ws_timeout_reject": 0,
        "openai_ws_late_discard": 0,
        "openai_ws_parse_fail": 0,
        "openai_ws_reconnects": 0,
        "openai_ws_http_fallback": 0,
        "openai_ws_request_id_mismatch": 0,
        "openai_ws_queue_wait_ms_values": [],
        "openai_ws_roundtrip_ms_values": [],
    }
    engine._responses_ws_pool = None
    engine.lock = threading.Lock()
    engine.cache_lock = threading.RLock()
    engine._analysis_cache = {}
    engine._gatekeeper_cache = {}
    engine.analysis_cache_ttl = 30.0
    engine.holding_analysis_cache_ttl = 60.0
    engine.gatekeeper_cache_ttl = 30.0
    engine.ai_disabled = False
    engine.consecutive_failures = 0
    engine.max_consecutive_failures = 5
    engine.last_call_time = 0.0
    engine.min_interval = 0.0
    return engine


def _sample_ws_data():
    return {
        "curr": 10100,
        "v_pw": 132.5,
        "fluctuation": 1.2,
        "ask_tot": 180000,
        "bid_tot": 150000,
        "net_ask_depth": -4200,
        "ask_depth_ratio": 93.5,
        "orderbook": {
            "asks": [
                {"price": 10110, "volume": 4500},
                {"price": 10120, "volume": 5500},
            ],
            "bids": [
                {"price": 10100, "volume": 3000},
                {"price": 10090, "volume": 4000},
            ],
        },
    }


def _sample_ticks():
    return [
        {"time": "09:00:10", "price": 10100, "volume": 220, "dir": "BUY", "strength": 135.0},
        {"time": "09:00:09", "price": 10100, "volume": 180, "dir": "BUY", "strength": 133.0},
        {"time": "09:00:08", "price": 10100, "volume": 160, "dir": "BUY", "strength": 131.0},
        {"time": "09:00:07", "price": 10095, "volume": 100, "dir": "SELL", "strength": 125.0},
        {"time": "09:00:06", "price": 10095, "volume": 90, "dir": "BUY", "strength": 122.0},
        {"time": "09:00:05", "price": 10090, "volume": 95, "dir": "BUY", "strength": 120.0},
        {"time": "09:00:00", "price": 10090, "volume": 80, "dir": "SELL", "strength": 119.0},
        {"time": "08:59:56", "price": 10085, "volume": 70, "dir": "BUY", "strength": 118.0},
        {"time": "08:59:52", "price": 10085, "volume": 60, "dir": "SELL", "strength": 117.0},
        {"time": "08:59:48", "price": 10080, "volume": 55, "dir": "BUY", "strength": 116.0},
    ]


def _sample_candles():
    return [
        {"체결시간": "08:56:00", "시가": 10020, "현재가": 10040, "고가": 10060, "저가": 10010, "거래량": 800},
        {"체결시간": "08:57:00", "시가": 10040, "현재가": 10060, "고가": 10080, "저가": 10030, "거래량": 900},
        {"체결시간": "08:58:00", "시가": 10060, "현재가": 10080, "고가": 10090, "저가": 10040, "거래량": 1000},
        {"체결시간": "08:59:00", "시가": 10080, "현재가": 10090, "고가": 10120, "저가": 10070, "거래량": 1200},
        {"체결시간": "09:00:00", "시가": 10090, "현재가": 10100, "고가": 10130, "저가": 10080, "거래량": 1600},
    ]


def test_openai_call_applies_endpoint_response_schema_when_flag_enabled(monkeypatch):
    engine = _build_engine()
    captured = {}

    def _fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            output_text='{"decision":"BUY","confidence":88,"order_type":"LIMIT_TOP","position_size_ratio":0.1,"invalidation_price":1000,"reasons":["ok"],"risks":[]}'
        )

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=True,
            OPENAI_TRANSPORT_MODE="http",
        ),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        schema_name="condition_entry_v1",
        endpoint_name="condition_entry",
        symbol="000001",
    )

    assert result["decision"] == "BUY"
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["name"] == "condition_entry_v1"
    assert captured["text"]["format"]["schema"] == OPENAI_RESPONSE_SCHEMA_REGISTRY["condition_entry_v1"]


def test_openai_deterministic_config_is_limited_to_json_path(monkeypatch):
    engine = _build_engine()
    calls = []

    def _fake_create(**kwargs):
        calls.append(kwargs)
        if "text" in kwargs:
            return SimpleNamespace(output_text='{"action":"BUY","score":91,"reason":"json"}')
        return SimpleNamespace(output_text="plain text report")

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=_fake_create))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED=True,
            OPENAI_TRANSPORT_MODE="http",
        ),
    )

    GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="json",
        endpoint_name="analyze_target",
        symbol="000001",
    )
    GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=False,
        context_name="text",
        endpoint_name="realtime_report",
        symbol="000001",
    )

    assert calls[0]["temperature"] == 0.0
    assert "text" in calls[0]
    assert calls[1]["temperature"] == 0.7
    assert "text" not in calls[1]


def test_openai_request_payload_omits_previous_response_id_by_default():
    engine = _build_engine()

    request = engine._build_openai_response_request(
        prompt="PROMPT",
        user_input="payload",
        require_json=True,
        context_name="ctx",
        model_name="gpt-fast",
        temperature=0.0,
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
        cache_key="abc",
    )
    payload = request.build_provider_payload(use_schema_registry=False)

    assert "previous_response_id" not in payload
    assert payload["metadata"]["request_id"] == request.request_id


def test_openai_analyze_target_timeout_rejects_buy_side_when_enabled(monkeypatch):
    engine = _build_engine()

    def _raise(*args, **kwargs):
        raise TimeoutError("ws timeout")

    monkeypatch.setattr(engine, "_call_openai_safe", _raise)
    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(openai_module.TRADING_RULES, OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED=True),
    )

    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["ai_parse_fail"] is True


def test_openai_responses_ws_pool_uses_round_robin_workers(monkeypatch):
    calls = []

    class _StubWorker:
        def __init__(self, *, worker_id, api_key, metrics_callback):
            self.worker_id = worker_id
            self.jobs = []
            calls.append(self)

        def submit(self, job):
            self.jobs.append(job.request.request_id)
            return OpenAITransportResult(payload={"worker_id": self.worker_id}, transport_mode="responses_ws", ws_used=True)

        def close(self):
            return None

    monkeypatch.setattr(openai_module, "OpenAIResponsesWSWorker", _StubWorker)

    pool = OpenAIResponsesWSPool(api_keys=["key-a"], pool_size=2, metrics_callback=None)

    for idx in range(3):
        request = OpenAIResponseRequest(
            prompt="PROMPT",
            user_input="payload",
            require_json=True,
            context_name="ctx",
            model_name="gpt-fast",
            temperature=0.0,
            schema_name="entry_v1",
            endpoint_name="analyze_target",
            request_id=f"req-{idx}",
            symbol="005930",
            cache_key="-",
            submitted_at_perf=0.0,
            timeout_ms=700,
        )
        pool.submit(request, use_schema_registry=False)

    assert len(calls[0].jobs) == 2
    assert len(calls[1].jobs) == 1


def test_openai_call_falls_back_from_ws_to_http(monkeypatch):
    engine = _build_engine()
    engine.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: None))

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
        ),
    )
    monkeypatch.setattr(engine, "_call_openai_responses_ws", lambda request: (_ for _ in ()).throw(TimeoutError("ws timeout")))
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_http",
        lambda request: OpenAITransportResult(
            payload={"action": "BUY", "score": 88, "reason": "http fallback"},
            transport_mode="http",
            ws_used=False,
            ws_http_fallback=True,
            roundtrip_ms=15,
        ),
    )

    result = GPTSniperEngine._call_openai_safe(
        engine,
        "PROMPT",
        "payload",
        require_json=True,
        context_name="test",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="005930",
    )
    meta = engine._consume_last_transport_meta()

    assert result["action"] == "BUY"
    assert meta["openai_ws_http_fallback"] is True
    assert meta["openai_transport_mode"] == "http"


def test_openai_ws_request_id_mismatch_fails_closed_without_http_fallback(monkeypatch):
    engine = _build_engine()

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        replace(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
            OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED=True,
        ),
    )
    monkeypatch.setattr(
        engine,
        "_call_openai_responses_ws",
        lambda request: (_ for _ in ()).throw(OpenAIWSRequestIdMismatchError("request_id mismatch")),
    )

    def _unexpected_http_fallback(request):
        raise AssertionError("request_id mismatch must not be converted to HTTP fallback")

    monkeypatch.setattr(engine, "_call_openai_responses_http", _unexpected_http_fallback)

    result = engine.analyze_target(
        "테스트",
        _sample_ws_data(),
        _sample_ticks(),
        _sample_candles(),
        strategy="SCALPING",
        prompt_profile="watching",
    )

    assert result["action"] == "DROP"
    assert result["score"] == 0
    assert result["ai_parse_fail"] is True
    assert result["openai_transport_mode"] == "responses_ws"
    assert result["openai_ws_used"] is True
    assert result["openai_ws_http_fallback"] is False
    assert result["openai_ws_error_type"] == "OpenAIWSRequestIdMismatchError"
