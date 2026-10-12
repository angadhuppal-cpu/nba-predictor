"""High-level functions that join data + model. Each returns a JSON-serialisable dict.

These back both the CLI and the tools Claude calls in chat mode.
"""

from __future__ import annotations

from . import data, model
from . import odds as oddsmath


def _team_ctx_safe(season: str | None = None):
    try:
        return data.get_team_context(season)
    except data.DataError:
        # Early in a season there may be no current-season team stats yet.
        try:
            return data.get_team_context(data.previous_season(season or data.current_season()))
        except data.DataError:
            return None


def _opp_abbr(opponent: str | None) -> str | None:
    return data.find_team(opponent)["abbreviation"] if opponent else None


def _context(player: dict, games, opponent: str | None) -> dict:
    latest = games.iloc[0]
    return {
        "player": player["full_name"],
        "team": latest["TEAM"],
        "opponent": opponent,
        "last_game": str(latest["GAME_DATE"].date()),
        "games_loaded": len(games),
    }


def analyze_prop(
    player: str,
    stat: str,
    line: float,
    over_odds: float | None = None,
    under_odds: float | None = None,
    opponent: str | None = None,
    home: bool | None = None,
    minutes_override: float | None = None,
    back_to_back: bool = False,
) -> dict:
    p, games = data.get_game_logs(player)
    opp = _opp_abbr(opponent)
    result = model.analyze_line(
        games, stat, line, over_odds=over_odds, under_odds=under_odds,
        opponent=opp, home=home, team_ctx=_team_ctx_safe(), minutes_override=minutes_override,
        back_to_back=back_to_back,
    )
    return {"context": _context(p, games, opp), **result}


def alt_lines(
    player: str,
    stat: str,
    offered: list[dict] | None = None,
    min_prob: float = 0.70,
    opponent: str | None = None,
    home: bool | None = None,
    minutes_override: float | None = None,
    back_to_back: bool = False,
) -> dict:
    p, games = data.get_game_logs(player)
    opp = _opp_abbr(opponent)
    result = model.alt_lines(
        games, stat, offered=offered, min_prob=min_prob,
        opponent=opp, home=home, team_ctx=_team_ctx_safe(), minutes_override=minutes_override,
        back_to_back=back_to_back,
    )
    return {"context": _context(p, games, opp), **result}


def compare_props(
    props: list[dict],
    opponent: str | None = None,
    home: bool | None = None,
) -> dict:
    """Analyse several props and rank them, best first.

    props: [{"player": ..., "stat": ..., "line": ..., "over_odds": ..., "under_odds": ..., "opponent": ...}]
    """
    ctx = _team_ctx_safe()
    rows = []
    for prop in props:
        try:
            p, games = data.get_game_logs(prop["player"])
            opp = _opp_abbr(prop.get("opponent", opponent))
            r = model.analyze_line(
                games, prop["stat"], prop["line"], prop.get("over_odds"), prop.get("under_odds"),
                opponent=opp, home=prop.get("home", home), team_ctx=ctx,
                minutes_override=prop.get("minutes_override"),
            )
            v = r["verdict"]
            ev = r["bet_evaluation"]["over" if v["pick"] == "OVER" else "under"]
            rows.append({
                "player": p["full_name"], "stat": r["projection"]["stat"], "line": prop["line"],
                "projected_mean": r["projection"]["projected_mean"], "pick": v["pick"],
                "hit_probability": v["hit_probability"], "strength": v["strength"],
                "edge_vs_market": ev["edge_vs_market"] if ev else None,
                "ev_per_1_unit": ev["ev_per_1_unit"] if ev else None,
                "last_10_over_pct": (r["hit_rates"]["last_10"] or {}).get("over_pct"),
            })
        except Exception as exc:  # keep going if one player fails
            rows.append({"player": prop.get("player"), "stat": prop.get("stat"), "error": str(exc)})
    ok = [r for r in rows if "error" not in r]
    ok.sort(key=lambda r: (r["edge_vs_market"] if r["edge_vs_market"] is not None else r["hit_probability"] - 0.524), reverse=True)
    return {"ranked": ok + [r for r in rows if "error" in r]}


def player_recent_games(player: str, n: int = 10) -> dict:
    p, games = data.get_game_logs(player)
    cols = ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "REB", "AST", "FG3M", "STL", "BLK", "TOV", "FGA", "FTA"]
    recent = games.head(n)[cols].copy()
    recent["GAME_DATE"] = recent["GAME_DATE"].dt.strftime("%Y-%m-%d")
    recent["MIN"] = recent["MIN"].round(1)
    season = games[games["SEASON"] == games["SEASON"].iloc[0]]
    averages = season[["MIN", "PTS", "REB", "AST", "FG3M", "STL", "BLK", "TOV"]].mean().round(2).to_dict()
    return {
        "player": p["full_name"],
        "season": games["SEASON"].iloc[0],
        "season_averages": averages,
        "season_games": len(season),
        "games": recent.to_dict("records"),
    }


def team_context(team: str) -> dict:
    ctx = _team_ctx_safe()
    if ctx is None:
        return {"error": "Team stats unavailable"}
    abbr = data.find_team(team)["abbreviation"]
    row = ctx.loc[abbr]
    ranks = {}
    for col in ["PACE", "DEF_RATING", "OFF_RATING", "OPP_PTS", "OPP_REB", "OPP_AST", "OPP_FG3M"]:
        if col in ctx.columns:
            # Rank 1 = most generous to opponents / fastest pace / worst defence.
            ranks[col] = int(ctx[col].rank(ascending=False, method="min").loc[abbr])
    league = {c: round(float(ctx[c].mean()), 2) for c in ranks}
    return {
        "team": abbr,
        "stats": {k: (round(float(v), 2) if isinstance(v, (int, float)) else v) for k, v in row.to_dict().items()},
        "rank_1_is_highest": ranks,
        "league_average": league,
    }


def head_to_head(player: str, opponent: str) -> dict:
    p, games = data.get_game_logs(player, seasons=None)
    opp = _opp_abbr(opponent)
    vs = games[games["OPP"] == opp]
    cols = ["GAME_DATE", "MATCHUP", "MIN", "PTS", "REB", "AST", "FG3M"]
    rows = vs[cols].copy()
    rows["GAME_DATE"] = rows["GAME_DATE"].dt.strftime("%Y-%m-%d")
    return {
        "player": p["full_name"], "opponent": opp, "games": len(vs),
        "averages": vs[["MIN", "PTS", "REB", "AST", "FG3M"]].mean().round(2).to_dict() if len(vs) else {},
        "log": rows.to_dict("records"),
    }


def backtest(player: str, stat: str, n_tests: int = 30) -> dict:
    p, games = data.get_game_logs(player)
    return {"player": p["full_name"], **model.backtest(games, stat, n_tests=n_tests)}


def odds_math(odds: list[float] | None = None, legs: list[dict] | None = None, prob: float | None = None) -> dict:
    out = {}
    if odds:
        out["odds"] = [{"american": o, "implied_prob": round(oddsmath.american_to_implied(o), 4),
                        "decimal": round(oddsmath.american_to_decimal(o), 3)} for o in odds]
        if len(odds) == 2:
            a, b = oddsmath.no_vig_probs(*odds)
            out["no_vig_probs"] = [round(a, 4), round(b, 4)]
            out["vig_pct"] = round(100 * (sum(oddsmath.american_to_implied(o) for o in odds) - 1), 2)
    if prob is not None:
        out["fair_american_odds_for_prob"] = oddsmath.prob_to_american(prob)
    if legs:
        out["parlay"] = oddsmath.parlay(legs)
    return out
