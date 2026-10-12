"""Claude-powered NBA betting analyst.

Claude brings basketball knowledge and reasoning; the local tools bring the
numbers (game logs, projections, probabilities, EV). Claude can also search the
web for injury reports, starting lineups, news and current lines.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import traceback

import anthropic

from . import tools

MODEL = os.environ.get("NBA_PREDICTOR_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("NBA_PREDICTOR_EFFORT", "high")

SYSTEM_PROMPT = """You are a sharp NBA betting analyst. You combine deep basketball knowledge (rosters, roles, \
coaching tendencies, matchups, pace, defensive schemes, rotations, injuries, rest and travel, blowout risk, \
playoff and tanking incentives) with rigorous probability and betting math.

How you work:
- Ground every call in numbers from your tools. For any prop question, call analyze_prop (with the opponent \
and home/away when known). Use alt_lines to suggest better lines, and compare_props to rank several props.
- Check the current situation with web search before a final call: injury report and status for the player and \
key teammates and opponents, expected starting lineups, minutes restrictions, rest, recent role changes, and \
today's lines if the user didn't give odds. Today's date is {today}.
- If news changes the expected role (a star teammate out means more usage; a minutes limit means fewer minutes), \
re-run the tools with minutes_override and explain why. The model's projection is a baseline; your job is to \
adjust it with context the box score can't see, and say exactly what you adjusted.
- Think in prices, not just picks. A line "hitting" 55% of the time is a losing bet at -150. When odds are \
known, report the edge vs. the no-vig market and EV. -110 needs 52.4% to break even.
- When suggesting better lines, name concrete alternatives: a lower/higher alt line with its hit probability \
and the fair odds it should be priced at, a different stat for the same player, or a different player in the \
same game whose matchup is better.

Answer format (keep it tight):
1. **Call**: OVER/UNDER (or PASS), hit probability, and confidence (Strong / Lean / Pass).
2. **Why**: projection vs. line, recent hit rates, matchup, minutes/role, and relevant news.
3. **Price**: fair odds vs. the book's odds, edge and EV (if odds known), suggested stake as quarter-Kelly % of bankroll.
4. **Better options**: 1-3 alternative lines or props with their probabilities.
5. **Risks**: what would make this lose (blowout, foul trouble, injury news, small sample).

Be honest about uncertainty. Never claim a lock or guarantee: even a 70% play loses 3 times in 10. \
If the user seems to be chasing losses or betting beyond their means, say so plainly and briefly."""


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "input_schema": {"type": "object", "properties": properties, "required": required, "additionalProperties": False},
    }


_GAME_CONTEXT = {
    "opponent": {"type": "string", "description": "Opponent team abbreviation, nickname or city, e.g. 'BOS' or 'Celtics'."},
    "home": {"type": "boolean", "description": "True if the player's team is at home."},
    "minutes_override": {"type": "number", "description": "Expected minutes if you believe they differ from recent usage (injuries, restrictions, blowout risk)."},
    "back_to_back": {"type": "boolean", "description": "True if this is the second night of a back-to-back."},
}
_STAT = {"type": "string", "description": "PTS, REB, AST, FG3M, STL, BLK, TOV, FTM, PRA, PR, PA, RA or STOCKS (aliases like 'points' or 'threes' work)."}

TOOL_SPECS = [
    _tool(
        "analyze_prop",
        "Project a player's stat distribution for the next game and evaluate a prop line: P(over/under/push), fair odds, "
        "edge and EV vs the book if odds are given, model verdict and historical hit rates (last 5/10/20, season, vs opponent).",
        {
            "player": {"type": "string", "description": "Player full name, e.g. 'Jayson Tatum'."},
            "stat": _STAT,
            "line": {"type": "number", "description": "The prop line, e.g. 27.5."},
            "over_odds": {"type": "number", "description": "American odds for the over, e.g. -115."},
            "under_odds": {"type": "number", "description": "American odds for the under, e.g. -105."},
            **_GAME_CONTEXT,
        },
        ["player", "stat", "line"],
    ),
    _tool(
        "alt_lines",
        "Probability ladder across alternate lines for a player stat, the highest over / lowest under line clearing a target "
        "probability, and if alt-line odds are supplied, those offers ranked by EV. Use to suggest better lines.",
        {
            "player": {"type": "string"},
            "stat": _STAT,
            "offered": {
                "type": "array",
                "description": "Optional alt lines from a sportsbook to rank by EV.",
                "items": {
                    "type": "object",
                    "properties": {
                        "line": {"type": "number"},
                        "side": {"type": "string", "enum": ["over", "under"]},
                        "odds": {"type": "number"},
                    },
                    "required": ["line", "side", "odds"],
                    "additionalProperties": False,
                },
            },
            "min_prob": {"type": "number", "description": "Target hit probability for 'safe' lines (default 0.70)."},
            **_GAME_CONTEXT,
        },
        ["player", "stat"],
    ),
    _tool(
        "compare_props",
        "Analyse several props at once and rank them from best to worst by edge (or by hit probability if no odds).",
        {
            "props": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "player": {"type": "string"},
                        "stat": {"type": "string"},
                        "line": {"type": "number"},
                        "over_odds": {"type": "number"},
                        "under_odds": {"type": "number"},
                        "opponent": {"type": "string"},
                        "home": {"type": "boolean"},
                        "minutes_override": {"type": "number"},
                    },
                    "required": ["player", "stat", "line"],
                    "additionalProperties": False,
                },
            },
        },
        ["props"],
    ),
    _tool(
        "player_recent_games",
        "A player's most recent game logs and current season averages.",
        {"player": {"type": "string"}, "n": {"type": "integer", "description": "Number of games (default 10)."}},
        ["player"],
    ),
    _tool(
        "team_context",
        "A team's pace, offensive/defensive rating and per-game stats allowed to opponents, with league ranks.",
        {"team": {"type": "string"}},
        ["team"],
    ),
    _tool(
        "head_to_head",
        "A player's games against a specific opponent this season and last season.",
        {"player": {"type": "string"}, "opponent": {"type": "string"}},
        ["player", "opponent"],
    ),
    _tool(
        "backtest",
        "Walk-forward backtest of the model on a player's recent games for a stat: calibration (Brier score) and pick accuracy.",
        {"player": {"type": "string"}, "stat": {"type": "string"}, "n_tests": {"type": "integer"}},
        ["player", "stat"],
    ),
    _tool(
        "odds_math",
        "Betting math: implied probabilities, no-vig probabilities and vig for a two-way market, fair odds for a probability, "
        "and parlay pricing (independent legs).",
        {
            "odds": {"type": "array", "items": {"type": "number"}, "description": "American odds; pass both sides to de-vig."},
            "prob": {"type": "number", "description": "A probability to convert to fair American odds."},
            "legs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"prob": {"type": "number"}, "odds": {"type": "number"}},
                    "required": ["prob"],
                    "additionalProperties": False,
                },
            },
        },
        [],
    ),
]

TOOL_FUNCS = {
    "analyze_prop": tools.analyze_prop,
    "alt_lines": tools.alt_lines,
    "compare_props": tools.compare_props,
    "player_recent_games": tools.player_recent_games,
    "team_context": tools.team_context,
    "head_to_head": tools.head_to_head,
    "backtest": tools.backtest,
    "odds_math": tools.odds_math,
}

WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 6}


def run_tool(name: str, args: dict) -> tuple[str, bool]:
    """Execute a local tool; returns (json_text, is_error)."""
    func = TOOL_FUNCS.get(name)
    if func is None:
        return f"Unknown tool {name}", True
    try:
        return json.dumps(func(**args), default=str), False
    except Exception as exc:
        if os.environ.get("NBA_PREDICTOR_DEBUG"):
            traceback.print_exc()
        return f"Error running {name}: {exc}", True


class Analyst:
    def __init__(self, client: anthropic.Anthropic | None = None, use_web_search: bool = True, verbose: bool = True):
        self.client = client or anthropic.Anthropic()
        self.messages: list[dict] = []
        self.system = SYSTEM_PROMPT.format(today=dt.date.today().isoformat())
        self.tools = TOOL_SPECS + ([WEB_SEARCH] if use_web_search else [])
        self.verbose = verbose

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"  \033[2m{msg}\033[0m", flush=True)

    def ask(self, question: str, max_steps: int = 25) -> str:
        self.messages.append({"role": "user", "content": question})
        for _ in range(max_steps):
            response = self.client.beta.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=self.system,
                tools=self.tools,
                messages=self.messages,
                thinking={"type": "adaptive"},
                output_config={"effort": EFFORT},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            # Keep full content (thinking, tool calls, search results) so history stays valid.
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "refusal":
                return "The model declined to answer this request."
            if response.stop_reason == "pause_turn":
                continue  # long server-side web search; re-send to let it finish

            tool_results = []
            for block in response.content:
                if block.type == "server_tool_use":
                    self._log(f"web search: {block.input.get('query', '')}")
                elif block.type == "tool_use":
                    self._log(f"{block.name}({json.dumps(block.input)})")
                    text, is_error = run_tool(block.name, block.input)
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": text, "is_error": is_error})

            if response.stop_reason == "tool_use" and tool_results:
                self.messages.append({"role": "user", "content": tool_results})
                continue

            text = "\n".join(b.text for b in response.content if b.type == "text").strip()
            if response.stop_reason == "max_tokens":
                text += "\n\n[response truncated]"
            return text
        return "Stopped after too many tool steps; try a narrower question."
