"""
Parlay evaluation + slate-wide edge scanner.

Builds on LineEvaluator to combine multiple prop legs into a single hit
probability and to find the best statistical edges across tonight's NBA
slate.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from line_evaluator import LineEvaluator, DB_PATH


def _conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path, check_same_thread=False)


# Same-game correlation discount (props in the same game aren't fully
# independent — e.g. usage spikes when a teammate goes off). Applied per
# additional leg from the same game.
SAME_GAME_DISCOUNT = 0.92


@dataclass
class ParlayLeg:
    player: str
    stat: str
    line: float
    direction: str
    opponent: Optional[str] = None
    american_odds: Optional[int] = None
    probability: Optional[float] = None
    recommendation: Optional[str] = None


def evaluate_parlay(
    evaluator: LineEvaluator,
    legs: List[Dict[str, Any]],
    correlation_discount: float = SAME_GAME_DISCOUNT,
) -> Dict[str, Any]:
    """Evaluate a multi-leg parlay. Returns combined probability + per-leg detail.

    legs: list of {player, stat, line, direction, opponent?, american_odds?}
    """
    if not legs:
        return {
            "legs": [],
            "combined_probability": None,
            "recommendation": "EMPTY",
            "warnings": ["No legs supplied."],
        }

    detailed_legs = []
    probabilities = []
    opponents_seen: Dict[str, int] = {}
    warnings: List[str] = []

    for raw in legs:
        try:
            ev = evaluator.evaluate_line(
                player_name=raw["player"],
                stat=raw["stat"],
                line=float(raw["line"]),
                opponent=raw.get("opponent"),
                direction=raw.get("direction", "over"),
                american_odds=raw.get("american_odds"),
            )
        except Exception as exc:
            detailed_legs.append({
                "player": raw.get("player"),
                "stat": raw.get("stat"),
                "line": raw.get("line"),
                "direction": raw.get("direction"),
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue

        ev_dict = ev.to_dict()
        detailed_legs.append(ev_dict)
        prob = ev_dict.get("blended_probability")
        if prob is None:
            warnings.append(
                f"No probability for {raw.get('player')} {raw.get('stat')} "
                f"{raw.get('direction')} {raw.get('line')}"
            )
            continue
        probabilities.append(prob)
        opp = ev_dict.get("vs_opponent_avg")  # not actually opponent — placeholder
        opponent = raw.get("opponent")
        if opponent:
            opponents_seen[opponent] = opponents_seen.get(opponent, 0) + 1

    if not probabilities:
        return {
            "legs": detailed_legs,
            "combined_probability": None,
            "recommendation": "INSUFFICIENT DATA",
            "warnings": warnings or ["No leg produced a probability."],
        }

    # Independent-legs combined prob, with correlation discount on extras
    # from the same game.
    combined = 1.0
    for p in probabilities:
        combined *= p
    extra_same_game = sum(max(0, c - 1) for c in opponents_seen.values())
    if extra_same_game > 0:
        combined *= correlation_discount ** extra_same_game

    rec = _parlay_recommendation(combined, len(legs))
    fair_odds = _decimal_to_american(1.0 / combined) if combined > 0 else None

    return {
        "legs": detailed_legs,
        "leg_count": len(legs),
        "combined_probability": round(combined, 4),
        "fair_american_odds": fair_odds,
        "same_game_legs": extra_same_game,
        "correlation_discount_applied": correlation_discount if extra_same_game > 0 else None,
        "recommendation": rec,
        "warnings": warnings,
    }


def _parlay_recommendation(prob: float, n_legs: int) -> str:
    # Rough thresholds — parlay variance is high, so be conservative.
    if prob >= 0.55:
        return "STRONG"
    if prob >= 0.40:
        return "PLAYABLE"
    if prob >= 0.25:
        return "DART"
    return "AVOID"


def _decimal_to_american(decimal_odds: float) -> int:
    if decimal_odds <= 0:
        return 0
    if decimal_odds >= 2.0:
        return int(round((decimal_odds - 1.0) * 100))
    return int(round(-100.0 / (decimal_odds - 1.0)))


# ---- Slate scanner ------------------------------------------------------------

def get_todays_games(db_path: str = DB_PATH,
                     date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return tonight's games from the local game_schedule table."""
    target = date or datetime.now().strftime("%Y-%m-%d")
    with _conn(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT game_id, date, time, home_team, away_team, status, arena
            FROM game_schedule
            WHERE date = ?
            ORDER BY time
            """,
            (target,),
        )
        rows = cur.fetchall()
    return [
        {
            "game_id": r[0], "date": r[1], "time": r[2],
            "home_team": r[3], "away_team": r[4],
            "status": r[5], "arena": r[6],
        }
        for r in rows
    ]


def top_players_for_team(team: str, limit: int = 5,
                         db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Return top scoring players on a team (current season)."""
    with _conn(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT player_name, points_avg, rebounds_avg, assists_avg, games_played
            FROM player_season_stats
            WHERE team = ? AND season = '2025-26' AND games_played >= 5
            ORDER BY points_avg DESC
            LIMIT ?
            """,
            (team, limit),
        )
        return [
            {
                "name": r[0], "ppg": r[1], "rpg": r[2],
                "apg": r[3], "games": r[4],
            }
            for r in cur.fetchall()
        ]


def scan_slate_for_edges(
    evaluator: LineEvaluator,
    date: Optional[str] = None,
    players_per_team: int = 4,
    top_n: int = 15,
) -> Dict[str, Any]:
    """Scan tonight's slate for the best statistical edges.

    Walks every game on the date, runs best_lines_for_player on the top
    scorers from each team versus the opponent they're actually playing, and
    aggregates the strongest edges across the league.
    """
    games = get_todays_games(date=date)
    if not games:
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "games": [],
            "edges": [],
            "message": "No games scheduled for this date in the local DB.",
        }

    edges: List[Dict[str, Any]] = []
    games_summary = []

    for g in games:
        home, away = g["home_team"], g["away_team"]
        home_players = top_players_for_team(home, limit=players_per_team)
        away_players = top_players_for_team(away, limit=players_per_team)

        for player in home_players:
            _accumulate_edges(evaluator, player["name"], away, home, edges)
        for player in away_players:
            _accumulate_edges(evaluator, player["name"], home, away, edges)

        games_summary.append({
            **g,
            "home_top_scorers": home_players,
            "away_top_scorers": away_players,
        })

    edges.sort(key=lambda e: abs(e.get("edge") or 0), reverse=True)
    return {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "games": games_summary,
        "edges": edges[:top_n],
    }


def _accumulate_edges(evaluator, player_name, opponent, team, sink):
    try:
        results = evaluator.best_lines_for_player(player_name, opponent=opponent)
    except Exception:
        return
    for r in results[:3]:  # top 3 per player to limit noise
        if abs(r.get("edge") or 0) < 0.10:
            continue
        sink.append({**r, "player": player_name, "team": team, "opponent": opponent})
