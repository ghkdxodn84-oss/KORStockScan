from __future__ import annotations

import json
import time

from src.engine.kiwoom_websocket import KiwoomWSManager
from src.utils import kiwoom_utils


class _FakeResponse:
    def __init__(self, token: str, *, status_code: int = 200, expires_in: int = 3600):
        self.status_code = status_code
        self.text = "OK"
        self._payload = {"access_token": token, "expires_in": expires_in}

    def json(self):
        return dict(self._payload)


def _config():
    return {
        "KIWOOM_BASE_URL": "https://example.test",
        "KIWOOM_APPKEY": "app-key-1234",
        "KIWOOM_SECRETKEY": "secret-key-5678",
    }


def _patch_cache_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("KIWOOM_TOKEN_CACHE_PATH", str(tmp_path / "kiwoom_token_cache.json"))
    monkeypatch.setenv("KIWOOM_TOKEN_LOCK_PATH", str(tmp_path / "kiwoom_token_cache.lock"))


def test_get_kiwoom_token_reuses_shared_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse("TOKEN_A")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}")

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_A"
    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_A"
    assert len(calls) == 1


def test_get_kiwoom_token_refreshes_expired_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    cache_path = tmp_path / "kiwoom_token_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cache_key": kiwoom_utils._token_cache_key(_config()),
                "access_token": "OLD_TOKEN",
                "issued_at": time.time() - 7200,
                "expires_at": time.time() - 60,
            }
        ),
        encoding="utf-8",
    )
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse("TOKEN_B")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}")

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_B"
    assert len(calls) == 1


def test_get_kiwoom_token_force_refresh_bypasses_valid_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse(f"TOKEN_{len(calls)}")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}")

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_1"
    assert kiwoom_utils.get_kiwoom_token(_config(), force_refresh=True) == "TOKEN_2"
    assert len(calls) == 2


def test_ws_token_refresh_uses_force_refresh(monkeypatch):
    calls = []

    def fake_get_token(conf, **kwargs):
        calls.append(kwargs)
        return "NEW_TOKEN"

    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", fake_get_token)

    manager = KiwoomWSManager("OLD_TOKEN")
    assert manager._refresh_ws_token() is True
    assert manager.token == "NEW_TOKEN"
    assert calls == [{"force_refresh": True}]
