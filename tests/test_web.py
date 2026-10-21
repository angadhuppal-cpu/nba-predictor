import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from nba_predictor import data, web


@pytest.fixture
def server(monkeypatch, tmp_path, games, team_ctx):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(web, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(data, "get_game_logs", lambda name, seasons=None, **kw: ({"full_name": "Test Player", "id": 1}, games))
    monkeypatch.setattr(data, "get_team_context", lambda season=None: team_ctx)
    app = web.App()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), web.make_handler(app, 0))
    port = srv.server_address[1]
    srv.RequestHandlerClass = web.make_handler(app, port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}", app
    srv.shutdown()


def call(base, path, body=None, host=None):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **({"Host": host} if host else {})})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_page_and_status(server):
    base, _ = server
    code, body = call(base, "/")
    assert code == 200 and b"NBA <span>Predictor" in body
    code, body = call(base, "/api/status")
    assert json.loads(body)["has_key"] is False


def test_rejects_foreign_host(server):
    base, _ = server
    code, _ = call(base, "/api/status", host="evil.example.com")
    assert code == 403


def test_key_roundtrip(server):
    base, _ = server
    code, body = call(base, "/api/key", {"key": "AIzaNotClaude"})
    assert code == 400 and "sk-ant-" in json.loads(body)["error"]
    code, body = call(base, "/api/key", {"key": "sk-ant-test-1234"})
    assert json.loads(body) == {"has_key": True, "key_hint": "...1234", "key_from_env": False}
    assert web.load_key() == "sk-ant-test-1234"
    call(base, "/api/key", {"key": ""})
    assert web.load_key() is None


def test_analyze_and_alt(server):
    base, _ = server
    code, body = call(base, "/api/analyze", {"player": "x", "stat": "PTS", "line": "24.5", "over_odds": "-110",
                                             "under_odds": "", "opponent": "LAL", "home": "away", "minutes": "", "b2b": False})
    r = json.loads(body)
    assert code == 200 and r["verdict"]["pick"] in ("OVER", "UNDER")
    assert r["bet_evaluation"]["under"] is None and r["projection"]["adjustment_factors"]["venue"] < 1
    code, body = call(base, "/api/alt", {"player": "x", "stat": "REB", "min_prob": "0.75", "home": "unknown"})
    assert code == 200 and json.loads(body)["ladder"]
    code, body = call(base, "/api/analyze", {"player": "x", "stat": "dunks", "line": 1})
    assert code == 400 and "Unsupported stat" in json.loads(body)["error"]


def test_chat_without_key(server):
    base, _ = server
    code, body = call(base, "/api/chat", {"session": "s", "message": "hi"})
    assert code == 400 and "API key" in json.loads(body)["error"]


def test_chat_failure_rolls_back_history(server, monkeypatch):
    base, app = server
    web.save_key("sk-ant-test")
    analyst = app.analyst("s")

    def boom(q):
        analyst.messages.append({"role": "user", "content": q})
        raise RuntimeError("network down")

    monkeypatch.setattr(analyst, "ask", boom)
    code, body = call(base, "/api/chat", {"session": "s", "message": "hi"})
    assert code == 400 and analyst.messages == []
