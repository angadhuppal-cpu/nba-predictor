import json
from types import SimpleNamespace

import pytest

from nba_predictor import __main__ as cli
from nba_predictor import agent, data, tools


@pytest.fixture(autouse=True)
def offline(monkeypatch, games, team_ctx):
    monkeypatch.setattr(data, "get_game_logs", lambda name, seasons=None, **kw: ({"full_name": "Test Player", "id": 1}, games))
    monkeypatch.setattr(data, "get_team_context", lambda season=None: team_ctx)


def test_analyze_prop_and_cli(capsys):
    r = tools.analyze_prop("test", "points", 24.5, -110, -110, opponent="Lakers", home=True)
    assert r["context"]["opponent"] == "LAL"
    json.dumps(r, default=str)
    cli.main(["analyze", "test", "PTS", "24.5", "--over", "-110", "--under", "-110", "--opp", "NYK", "--away"])
    out = capsys.readouterr().out
    assert ">>>" in out and "P(over)" in out
    cli.main(["alt", "test", "REB"])
    assert "P(under)" in capsys.readouterr().out


def test_compare_and_misc():
    r = tools.compare_props([
        {"player": "a", "stat": "PTS", "line": 15.5, "over_odds": -110, "under_odds": -110},
        {"player": "b", "stat": "PTS", "line": 25.5, "over_odds": -110, "under_odds": -110},
    ])
    assert r["ranked"][0]["line"] == 15.5
    assert tools.team_context("BOS")["team"] == "BOS"
    assert tools.head_to_head("a", "MIA")["games"] > 0
    assert tools.player_recent_games("a", 5)["games"].__len__() == 5
    assert tools.odds_math(odds=[-110, -110])["vig_pct"] == pytest.approx(4.76, abs=0.01)


def test_run_tool_reports_errors():
    text, err = agent.run_tool("analyze_prop", {"player": "x", "stat": "dunks", "line": 1})
    assert err and "Unsupported stat" in text
    text, err = agent.run_tool("analyze_prop", {"player": "x", "stat": "PTS", "line": 20.5})
    assert not err and json.loads(text)["verdict"]


class FakeClient:
    """Mimics client.beta.messages.create: first asks for a tool, then answers."""

    def __init__(self):
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        if len(self.calls) == 1:
            block = SimpleNamespace(type="tool_use", id="t1", name="analyze_prop",
                                    input={"player": "x", "stat": "PTS", "line": 24.5})
            return SimpleNamespace(stop_reason="tool_use", content=[block])
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="**Call**: OVER")])


def test_agent_loop():
    fake = FakeClient()
    a = agent.Analyst(client=fake, verbose=False)
    assert a.ask("Will x go over 24.5?") == "**Call**: OVER"
    second = fake.calls[1]
    assert second["messages"][-1]["content"][0]["type"] == "tool_result"
    assert second["fallbacks"] == "default"
    assert any(t.get("type") == "web_search_20260209" for t in second["tools"])
