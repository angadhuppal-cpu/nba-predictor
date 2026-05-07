"""
NBA Gambling Line AI Advisor — pluggable LLM backend.

Wraps an LLM (Claude or Gemini) with tool-use access to the local
LineEvaluator and database. The model brings NBA knowledge + math
reasoning; the tools deliver real numbers from your game-log database.

Pick the provider via the LLM_PROVIDER env var:
  - "gemini"  (default) — uses google-genai, free tier friendly
  - "claude"            — uses anthropic, more capable but paid

Required env keys:
  - GEMINI_API_KEY  (for gemini)        https://aistudio.google.com/apikey
  - ANTHROPIC_API_KEY (for claude)      https://console.anthropic.com/
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from line_evaluator import LineEvaluator


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


# Tool catalog (Anthropic-style JSON schemas; Gemini wrapper converts them).
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
                "games": {"type": "integer"},
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
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
]


def _eval_to_summary(ev_dict: Dict[str, Any]) -> Dict[str, Any]:
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


class _BaseAdvisor:
    """Provider-agnostic plumbing — tool execution + tool catalog."""

    def __init__(self, evaluator: Optional[LineEvaluator] = None):
        self.evaluator = evaluator or LineEvaluator()

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

    def chat(self, user_message: str,
             history: Optional[List[Any]] = None,
             max_iterations: int = 8) -> Dict[str, Any]:
        raise NotImplementedError


# ---- Claude (Anthropic) backend ------------------------------------------------

class ClaudeAdvisor(_BaseAdvisor):
    DEFAULT_MODEL = "claude-opus-4-7"

    def __init__(self, evaluator: Optional[LineEvaluator] = None,
                 api_key: Optional[str] = None,
                 model: Optional[str] = None):
        super().__init__(evaluator)
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError(
                "The 'anthropic' package is not installed. Run: pip install anthropic"
            ) from e
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to backend/.env or your shell."
            )
        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=key)
        self.model = model or os.environ.get("NBA_AI_MODEL", self.DEFAULT_MODEL)

    def chat(self, user_message, history=None, max_iterations=8):
        messages: List[Dict[str, Any]] = list(history or [])
        messages.append({"role": "user", "content": user_message})
        tool_calls: List[Dict[str, Any]] = []

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=[{
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }],
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                reply = "".join(
                    b.text for b in response.content if getattr(b, "type", None) == "text"
                ).strip()
                return {"reply": reply, "history": messages,
                        "tool_calls": tool_calls, "stop_reason": "end_turn"}

            if response.stop_reason != "tool_use":
                reply = "".join(
                    b.text for b in response.content if getattr(b, "type", None) == "text"
                ).strip() or f"(model stopped: {response.stop_reason})"
                return {"reply": reply, "history": messages,
                        "tool_calls": tool_calls, "stop_reason": response.stop_reason}

            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                result = self._execute_tool(block.name, dict(block.input))
                tool_calls.append({"name": block.name, "input": dict(block.input), "result": result})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })
            messages.append({"role": "user", "content": tool_results})

        return {"reply": "Stopped: hit max tool-use iterations.",
                "history": messages, "tool_calls": tool_calls,
                "stop_reason": "max_iterations"}


# ---- Gemini (google-genai) backend --------------------------------------------

def _strip_for_gemini(schema: Any) -> Any:
    """Remove JSON-schema fields Gemini's tool validator rejects."""
    if isinstance(schema, dict):
        return {k: _strip_for_gemini(v)
                for k, v in schema.items()
                if k not in ("default", "additionalProperties", "$schema")}
    if isinstance(schema, list):
        return [_strip_for_gemini(v) for v in schema]
    return schema


class GeminiAdvisor(_BaseAdvisor):
    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, evaluator: Optional[LineEvaluator] = None,
                 api_key: Optional[str] = None,
                 model: Optional[str] = None):
        super().__init__(evaluator)
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise RuntimeError(
                "The 'google-genai' package is not installed. Run: pip install google-genai"
            ) from e
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey"
            )
        self._genai = genai
        self._types = types
        self.client = genai.Client(api_key=key)
        self.model = model or os.environ.get("NBA_AI_MODEL", self.DEFAULT_MODEL)
        self._tools = self._build_tools()

    def _build_tools(self):
        decls = []
        for t in TOOL_DEFINITIONS:
            decls.append({
                "name": t["name"],
                "description": t["description"],
                "parameters": _strip_for_gemini(t["input_schema"]),
            })
        return [self._types.Tool(function_declarations=decls)]

    def chat(self, user_message, history=None, max_iterations=8):
        types = self._types
        contents = list(history or [])
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        ))
        tool_calls: List[Dict[str, Any]] = []

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=self._tools,
        )

        for _ in range(max_iterations):
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            if not response.candidates:
                return {"reply": "(no response from model)",
                        "history": contents, "tool_calls": tool_calls,
                        "stop_reason": "no_candidates"}

            candidate = response.candidates[0]
            model_content = candidate.content
            if model_content is None:
                return {"reply": "(empty model content)",
                        "history": contents, "tool_calls": tool_calls,
                        "stop_reason": "empty"}
            contents.append(model_content)

            function_calls = [p.function_call for p in (model_content.parts or [])
                              if getattr(p, "function_call", None)]

            if not function_calls:
                reply = "".join(
                    p.text for p in (model_content.parts or [])
                    if getattr(p, "text", None)
                ).strip()
                return {"reply": reply, "history": contents,
                        "tool_calls": tool_calls, "stop_reason": "end_turn"}

            response_parts = []
            for fc in function_calls:
                args = dict(fc.args) if fc.args else {}
                result = self._execute_tool(fc.name, args)
                tool_calls.append({"name": fc.name, "input": args, "result": result})
                response_parts.append(types.Part.from_function_response(
                    name=fc.name,
                    response={"result": result},
                ))
            contents.append(types.Content(role="user", parts=response_parts))

        return {"reply": "Stopped: hit max tool-use iterations.",
                "history": contents, "tool_calls": tool_calls,
                "stop_reason": "max_iterations"}


# ---- Factory ------------------------------------------------------------------

def get_advisor(evaluator: Optional[LineEvaluator] = None,
                provider: Optional[str] = None) -> _BaseAdvisor:
    """Return an advisor for the configured provider.

    Provider precedence:
      1. explicit `provider` argument
      2. LLM_PROVIDER env var
      3. whichever API key is set (Gemini wins ties — it's the free default)
    """
    explicit = (provider or os.environ.get("LLM_PROVIDER", "")).strip().lower()
    if not explicit:
        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            explicit = "gemini"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            explicit = "claude"
        else:
            explicit = "gemini"

    if explicit in ("gemini", "google"):
        return GeminiAdvisor(evaluator=evaluator)
    if explicit in ("claude", "anthropic"):
        return ClaudeAdvisor(evaluator=evaluator)
    raise RuntimeError(
        f"Unknown LLM_PROVIDER '{explicit}'. Use 'gemini' or 'claude'."
    )


# Backwards-compatible alias.
NBALineAdvisor = ClaudeAdvisor
