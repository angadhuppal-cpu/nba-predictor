"""
NBA Gambling Line AI Advisor

Wraps Claude (claude-opus-4-7) with tool-use access to the local LineEvaluator
and database. The model brings NBA domain knowledge + math/probability
reasoning; the tools deliver the actual numbers from your game-log database
and prediction system.

Conversational interface: ask "is LeBron's 24.5 points line gonna hit
tonight vs BOS?" and the model calls the right tools, reasons through the
result, and returns a recommendation.

Requires ANTHROPIC_API_KEY in the environment.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore

from line_evaluator import LineEvaluator


MODEL = os.environ.get("NBA_AI_MODEL", "claude-opus-4-7")


SYSTEM_PROMPT = """You are an expert NBA betting analyst with two specialties:

1. **Deep NBA knowledge** — players, teams, lineups, coaching, schedule context,
   matchup history, injury impacts, role changes, and pace/defense dynamics.
2. **Statistics and probability** — hit rates, normal/empirical distributions,
   variance, sample-size discipline, edge vs implied probability, and Kelly
   sizing intuition.

The user will ask whether a sportsbook prop line will hit (e.g.
"Will Luka go OVER 32.5 points tonight vs Memphis?") or ask you to find the
best lines for a player tonight. You have tools that query a local NBA
database with game logs, season stats, team defensive ratings, and an injury
report. ALWAYS call tools to get real numbers — never guess at averages.

Workflow for any line question:
- Identify the player, stat, line, direction (over/under), and opponent if given.
- Call `evaluate_line` to get the statistical hit probability and edge.
- For context, call `get_team_defense` (opponent) and `get_active_injuries`
  for both teams when relevant — a star teammate being out changes usage rate
  significantly. Use `get_player_recent_form` if you need to see specific games.
- For "find me a better line" requests, use `find_best_lines`.

In your final response:
- State the recommendation clearly (HIT / MISS / PASS) with a confidence level.
- Show the blended probability and the key drivers (last-10 avg, vs-opponent
  avg, projection, normal-model probability).
- Cite specific NBA context that the pure stats don't capture (matchup,
  injuries, role, pace, schedule spot).
- When stats and context disagree, explain the disagreement and pick the
  side you find more credible.
- ALWAYS include a brief responsible-gambling note at the end.

Be concise. Lead with the recommendation. Use bullet points for the math.
Never invent numbers — if a tool didn't return data, say so.
"""


def _eval_to_summary(ev_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Trim the LineEvaluation dict to fields useful for the model."""
    keep = {
        "player", "stat_label", "line", "direction",
        "sample_size", "recent_sample_size",
        "season_avg", "recent_avg", "vs_opponent_avg",
        "home_avg", "away_avg", "std_dev", "projection",
        "hit_rate_season", "hit_rate_recent", "hit_rate_vs_opponent",
        "prob_normal_model", "blended_probability",
        "edge_vs_line", "edge_vs_implied",
        "recommendation", "confidence", "reasoning", "warnings",
    }
    return {k: v for k, v in ev_dict.items() if k in keep}


TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "evaluate_line",
        "description": (
            "Evaluate a sportsbook prop line for an NBA player. Returns hit "
            "probability, edge, and a recommendation built from historical "
            "game logs, recent form, vs-opponent splits, and a normal "
            "distribution model. Use this for ANY 'will line X hit' question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "player_name": {"type": "string", "description": "Full player name as it appears in the NBA, e.g. 'LeBron James'."},
                "stat": {
                    "type": "string",
                    "description": "One of: points, rebounds, assists, threes, steals, blocks, pra (P+R+A), pr (P+R), pa (P+A), ra (R+A).",
                },
                "line": {"type": "number", "description": "The book's line, e.g. 24.5"},
                "direction": {
                    "type": "string",
                    "enum": ["over", "under"],
                    "description": "Which side of the line the user is asking about.",
                },
                "opponent": {
                    "type": "string",
                    "description": "Opponent team abbreviation (BOS, LAL, etc.). Optional but improves accuracy.",
                },
                "american_odds": {
                    "type": "integer",
                    "description": "Optional. American odds attached to the line (e.g. -110, +135). If supplied, edge_vs_implied is computed.",
                },
            },
            "required": ["player_name", "stat", "line", "direction"],
        },
    },
    {
        "name": "find_best_lines",
        "description": (
            "Scan a grid of common prop lines for a player and return the ones "
            "with the largest statistical edge. Use when the user asks for "
            "'better lines' or 'best plays' for a player."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "player_name": {"type": "string"},
                "opponent": {"type": "string", "description": "Optional opponent team abbreviation."},
            },
            "required": ["player_name"],
        },
    },
    {
        "name": "get_player_recent_form",
        "description": "Return the player's last N game logs (default 10) with averages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "player_name": {"type": "string"},
                "games": {"type": "integer", "default": 10},
            },
            "required": ["player_name"],
        },
    },
    {
        "name": "get_team_defense",
        "description": "Defensive context for a team: defensive rating, pace, opponent FG%/3P%, record.",
        "input_schema": {
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Team abbreviation, e.g. 'BOS'."},
            },
            "required": ["team"],
        },
    },
    {
        "name": "get_active_injuries",
        "description": "Return current injury report. Filter by team (abbreviation) or pass nothing for league-wide.",
        "input_schema": {
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Optional team abbreviation."},
            },
        },
    },
    {
        "name": "search_players",
        "description": "Search the player database by partial name. Use when the user gives a nickname or partial name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
]


class NBALineAdvisor:
    """Conversational AI advisor over the LineEvaluator tools."""

    def __init__(self, evaluator: Optional[LineEvaluator] = None,
                 api_key: Optional[str] = None,
                 model: str = MODEL):
        if anthropic is None:
            raise RuntimeError(
                "The 'anthropic' package is not installed. Run: pip install anthropic"
            )
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to backend/.env or your shell."
            )
        self.client = anthropic.Anthropic(api_key=key)
        self.evaluator = evaluator or LineEvaluator()
        self.model = model

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        try:
            if name == "evaluate_line":
                ev = self.evaluator.evaluate_line(
                    player_name=args["player_name"],
                    stat=args["stat"],
                    line=float(args["line"]),
                    opponent=args.get("opponent"),
                    direction=args.get("direction", "over"),
                    american_odds=args.get("american_odds"),
                )
                return _eval_to_summary(ev.to_dict())
            if name == "find_best_lines":
                return self.evaluator.best_lines_for_player(
                    player_name=args["player_name"],
                    opponent=args.get("opponent"),
                )
            if name == "get_player_recent_form":
                return self.evaluator.get_player_form(
                    player_name=args["player_name"],
                    games=args.get("games", 10),
                )
            if name == "get_team_defense":
                return self.evaluator.get_team_defense(args["team"]) or {
                    "error": f"No team-stats row found for {args['team']}"
                }
            if name == "get_active_injuries":
                return self.evaluator.get_active_injuries(args.get("team"))
            if name == "search_players":
                return self.evaluator.list_players(
                    query=args.get("query", ""),
                    limit=args.get("limit", 10),
                )
            return {"error": f"Unknown tool: {name}"}
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}

    def chat(
        self,
        user_message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        max_iterations: int = 8,
    ) -> Dict[str, Any]:
        """Run one user turn through the agentic tool-use loop.

        Returns {'reply': str, 'history': [...], 'tool_calls': [...]} so the
        caller can render the answer and feed `history` back on the next turn.
        """
        messages: List[Dict[str, Any]] = list(history or [])
        messages.append({"role": "user", "content": user_message})

        tool_calls: List[Dict[str, Any]] = []

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            # Append the assistant turn (preserve tool_use blocks for follow-ups)
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                reply = "".join(
                    b.text for b in response.content if getattr(b, "type", None) == "text"
                ).strip()
                return {
                    "reply": reply,
                    "history": messages,
                    "tool_calls": tool_calls,
                    "stop_reason": response.stop_reason,
                }

            if response.stop_reason != "tool_use":
                # Refusal, max_tokens, or something else — surface and stop.
                reply = "".join(
                    b.text for b in response.content if getattr(b, "type", None) == "text"
                ).strip() or f"(model stopped: {response.stop_reason})"
                return {
                    "reply": reply,
                    "history": messages,
                    "tool_calls": tool_calls,
                    "stop_reason": response.stop_reason,
                }

            # Execute every tool_use block in this turn.
            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                result = self._execute_tool(block.name, dict(block.input))
                tool_calls.append({
                    "name": block.name,
                    "input": dict(block.input),
                    "result": result,
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })
            messages.append({"role": "user", "content": tool_results})

        return {
            "reply": "Stopped: hit max tool-use iterations.",
            "history": messages,
            "tool_calls": tool_calls,
            "stop_reason": "max_iterations",
        }
