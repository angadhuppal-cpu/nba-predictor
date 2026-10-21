"""Local browser app: `python -m nba_predictor web` (or double-click the launcher).

Runs a small web server on 127.0.0.1 only (never reachable from other machines)
and opens the page in your browser. The Claude API key is pasted into the page
once and saved to ~/.nba_predictor/config.json on this computer.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import traceback
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import data, tools

CONFIG_PATH = Path(os.environ.get("NBA_PREDICTOR_CONFIG", Path.home() / ".nba_predictor" / "config.json"))
PAGE_PATH = Path(__file__).with_name("static") / "index.html"
DEFAULT_PORT = 8765


def load_key() -> str | None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    try:
        return json.loads(CONFIG_PATH.read_text()).get("anthropic_api_key") or None
    except (OSError, ValueError):
        return None


def save_key(key: str | None) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        cfg = json.loads(CONFIG_PATH.read_text())
    except (OSError, ValueError):
        cfg = {}
    if key:
        cfg["anthropic_api_key"] = key
    else:
        cfg.pop("anthropic_api_key", None)
    CONFIG_PATH.write_text(json.dumps(cfg))
    try:
        CONFIG_PATH.chmod(0o600)  # readable only by you
    except OSError:
        pass


def _num(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    return float(v)


def _game_kwargs(body: dict) -> dict:
    home = body.get("home")
    return {
        "opponent": (body.get("opponent") or "").strip() or None,
        "home": None if home in (None, "", "unknown") else home in (True, "home"),
        "minutes_override": _num(body.get("minutes")),
        "back_to_back": bool(body.get("b2b")),
    }


class App:
    """Holds one AI conversation per browser tab."""

    def __init__(self):
        self.sessions: dict[str, object] = {}
        self.lock = threading.Lock()

    def analyst(self, session: str):
        from .agent import Analyst
        import anthropic

        with self.lock:
            a = self.sessions.get(session)
            if a is None:
                key = load_key()
                if not key:
                    raise PermissionError("Add your Claude API key first (Settings, top right).")
                a = Analyst(client=anthropic.Anthropic(api_key=key), verbose=False)
                self.sessions[session] = a
            return a

    def chat(self, body: dict) -> dict:
        import anthropic

        question = (body.get("message") or "").strip()
        if not question:
            raise ValueError("Type a question first.")
        a = self.analyst(body.get("session") or "default")
        before = len(a.messages)
        try:
            answer = a.ask(question)
        except anthropic.AuthenticationError:
            del a.messages[before:]
            self.reset_all()
            raise PermissionError("Claude rejected the API key. Check it in Settings.")
        except anthropic.PermissionDeniedError:
            del a.messages[before:]
            raise PermissionError("Your Claude account can't use this model yet. Check billing/credits at console.anthropic.com.")
        except anthropic.RateLimitError:
            del a.messages[before:]
            raise RuntimeError("Claude rate limit hit. Wait a minute and try again.")
        except anthropic.APIConnectionError:
            del a.messages[before:]
            raise RuntimeError("Couldn't reach Claude. Check your internet connection.")
        except Exception:
            del a.messages[before:]  # drop the failed turn so the conversation stays valid
            raise
        return {"answer": answer, "steps": a.steps}

    def reset(self, body: dict) -> dict:
        with self.lock:
            self.sessions.pop(body.get("session") or "default", None)
        return {"ok": True}

    def reset_all(self) -> None:
        with self.lock:
            self.sessions.clear()

    def status(self, _body=None) -> dict:
        key = load_key()
        return {"has_key": bool(key), "key_hint": f"...{key[-4:]}" if key else None,
                "key_from_env": bool(os.environ.get("ANTHROPIC_API_KEY"))}

    def set_key(self, body: dict) -> dict:
        key = (body.get("key") or "").strip()
        if key and not key.startswith("sk-ant-"):
            raise ValueError("That doesn't look like a Claude API key. They start with 'sk-ant-' (get one at console.anthropic.com).")
        save_key(key or None)
        self.reset_all()
        return self.status()

    def analyze(self, body: dict) -> dict:
        return tools.analyze_prop(
            body["player"], body["stat"], float(body["line"]),
            _num(body.get("over_odds")), _num(body.get("under_odds")), **_game_kwargs(body),
        )

    def alt(self, body: dict) -> dict:
        return tools.alt_lines(body["player"], body["stat"], None, _num(body.get("min_prob")) or 0.70, **_game_kwargs(body))


def make_handler(app: App, port: int):
    routes = {
        "/api/status": app.status, "/api/key": app.set_key, "/api/chat": app.chat,
        "/api/reset": app.reset, "/api/analyze": app.analyze, "/api/alt": app.alt,
    }
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the launcher window quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj) -> None:
            self._send(code, json.dumps(obj, default=str).encode(), "application/json")

        def _host_ok(self) -> bool:
            # Blocks other websites from talking to this server via DNS rebinding.
            return self.headers.get("Host", "") in allowed_hosts

        def do_GET(self):
            if not self._host_ok():
                return self._send(403, b"Forbidden", "text/plain")
            if self.path in ("/", "/index.html"):
                return self._send(200, PAGE_PATH.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/status":
                return self._json(200, app.status())
            self._send(404, b"Not found", "text/plain")

        def do_POST(self):
            if not self._host_ok():
                return self._send(403, b"Forbidden", "text/plain")
            func = routes.get(self.path)
            if func is None:
                return self._json(404, {"error": "Not found"})
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
                self._json(200, func(body))
            except (PermissionError, ValueError, KeyError, data.DataError, RuntimeError) as exc:
                msg = f"Missing field: {exc}" if isinstance(exc, KeyError) else str(exc)
                self._json(400, {"error": msg})
            except Exception as exc:
                traceback.print_exc()
                self._json(500, {"error": f"Something went wrong: {exc}"})

    return Handler


def _free_port(preferred: int) -> int:
    for port in [preferred, *range(preferred + 1, preferred + 20)]:
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(port: int = DEFAULT_PORT, open_browser: bool = True) -> None:
    port = _free_port(port)
    app = App()
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app, port))
    url = f"http://localhost:{port}"
    print(f"\n  NBA Predictor is running at {url}")
    print("  Keep this window open while you use it. Close it (or press Ctrl+C) to stop.\n")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
