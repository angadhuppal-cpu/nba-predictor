"""
NBA Prop Line Evaluator

Pure-statistics engine for evaluating sportsbook prop lines (points, rebounds,
assists, threes made, and combos). Computes hit probability from historical
game logs using both empirical hit-rate and a normal-distribution model, then
combines that with the existing EliteNBAPredictor projection to produce an
edge and a recommendation.

This module is the deterministic "math brain" the AI advisor calls into.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, asdict, field
from datetime import datetime
from math import sqrt, erf
from typing import Optional, List, Dict, Any


DB_PATH = os.environ.get(
    "NBA_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "database", "nba_data.db"),
)


# stat_key -> (column expression, friendly label)
STAT_COLUMNS: Dict[str, tuple] = {
    "points": ("points", "Points"),
    "rebounds": ("rebounds", "Rebounds"),
    "assists": ("assists", "Assists"),
    "threes": ("three_pointers_made", "3PT Made"),
    "steals": ("steals", "Steals"),
    "blocks": ("blocks", "Blocks"),
    "pra": ("(points + rebounds + assists)", "Points+Rebounds+Assists"),
    "pr": ("(points + rebounds)", "Points+Rebounds"),
    "pa": ("(points + assists)", "Points+Assists"),
    "ra": ("(rebounds + assists)", "Rebounds+Assists"),
}

STAT_ALIASES = {
    "pts": "points",
    "reb": "rebounds",
    "rebs": "rebounds",
    "ast": "assists",
    "asts": "assists",
    "3pm": "threes",
    "3pt": "threes",
    "threepointers": "threes",
    "stl": "steals",
    "blk": "blocks",
    "p+r+a": "pra",
    "p+r": "pr",
    "p+a": "pa",
    "r+a": "ra",
}


def normalize_stat(stat: str) -> str:
    s = stat.lower().strip().replace(" ", "")
    s = STAT_ALIASES.get(s, s)
    if s not in STAT_COLUMNS:
        raise ValueError(
            f"Unknown stat '{stat}'. Valid: {', '.join(STAT_COLUMNS.keys())}"
        )
    return s


def normal_cdf(x: float, mu: float, sigma: float) -> float:
    """Standard-normal CDF P(X <= x) via erf."""
    if sigma <= 0:
        return 1.0 if x >= mu else 0.0
    return 0.5 * (1.0 + erf((x - mu) / (sigma * sqrt(2.0))))


def implied_prob_from_american_odds(odds: int) -> float:
    """Convert American odds to implied probability (no vig removal)."""
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return -odds / (-odds + 100.0)


@dataclass
class LineEvaluation:
    player: str
    stat: str
    stat_label: str
    line: float
    direction: str  # 'over' or 'under'
    sample_size: int
    recent_sample_size: int
    season_avg: Optional[float]
    recent_avg: Optional[float]
    vs_opponent_avg: Optional[float]
    home_avg: Optional[float]
    away_avg: Optional[float]
    std_dev: Optional[float]
    projection: Optional[float]
    hit_rate_season: Optional[float]
    hit_rate_recent: Optional[float]
    hit_rate_vs_opponent: Optional[float]
    prob_normal_model: Optional[float]
    blended_probability: Optional[float]
    edge_vs_line: Optional[float]
    edge_vs_implied: Optional[float]
    recommendation: str
    confidence: str  # 'low' | 'medium' | 'high'
    reasoning: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LineEvaluator:
    """Evaluate sportsbook prop lines against a player's game-log history."""

    # Number of most-recent games to treat as "recent form".
    RECENT_GAMES = 10
    # Minimum sample we need before trusting a stat.
    MIN_SAMPLE = 5

    def __init__(self, db_path: str = DB_PATH, predictor=None):
        self.db_path = db_path
        self.predictor = predictor

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _fetch_games(
        self,
        player_name: str,
        stat_expr: str,
        opponent: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        sql = f"""
            SELECT date, opponent, is_home, minutes,
                   {stat_expr} AS stat_value
            FROM player_stats
            WHERE player_name = ?
        """
        params: List[Any] = [player_name]
        if opponent:
            sql += " AND opponent = ?"
            params.append(opponent)
        sql += " ORDER BY date DESC"

        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()

        return [
            {
                "date": r[0],
                "opponent": r[1],
                "is_home": bool(r[2]) if r[2] is not None else None,
                "minutes": r[3],
                "value": r[4],
            }
            for r in rows
            if r[4] is not None
        ]

    def list_players(self, query: str = "", limit: int = 25) -> List[Dict[str, Any]]:
        """Search the player_season_stats table for player names."""
        with self._conn() as conn:
            cur = conn.cursor()
            if query:
                cur.execute(
                    """
                    SELECT DISTINCT player_name, team, points_avg, games_played
                    FROM player_season_stats
                    WHERE player_name LIKE ? AND season = '2025-26'
                    ORDER BY points_avg DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", limit),
                )
            else:
                cur.execute(
                    """
                    SELECT DISTINCT player_name, team, points_avg, games_played
                    FROM player_season_stats
                    WHERE season = '2025-26' AND games_played >= 5
                    ORDER BY points_avg DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            return [
                {"name": r[0], "team": r[1], "ppg": r[2], "games": r[3]}
                for r in cur.fetchall()
            ]

    def get_player_form(self, player_name: str, games: int = 10) -> Dict[str, Any]:
        """Return the player's recent game log across all box-score stats."""
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT date, opponent, is_home, minutes, points, rebounds, assists,
                       steals, blocks, three_pointers_made, turnovers
                FROM player_stats
                WHERE player_name = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (player_name, games),
            )
            rows = cur.fetchall()

        keys = [
            "date", "opponent", "is_home", "minutes", "points", "rebounds",
            "assists", "steals", "blocks", "threes", "turnovers",
        ]
        recent = [dict(zip(keys, row)) for row in rows]
        if not recent:
            return {"player": player_name, "games": [], "averages": {}}

        avg_keys = ["minutes", "points", "rebounds", "assists", "steals",
                    "blocks", "threes", "turnovers"]
        averages = {}
        for k in avg_keys:
            vals = [g[k] for g in recent if g[k] is not None]
            averages[k] = round(sum(vals) / len(vals), 2) if vals else None
        return {"player": player_name, "games": recent, "averages": averages}

    def get_team_defense(self, team: str) -> Optional[Dict[str, Any]]:
        """Return defensive context for a team (latest season row)."""
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT team_name, season, defensive_rating, pace, opp_points_pg,
                       opp_fg_pct, opp_three_pct, wins, losses
                FROM team_stats
                WHERE team_name = ? OR team_id = ?
                ORDER BY season DESC
                LIMIT 1
                """,
                (team, team),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "team": row[0],
            "season": row[1],
            "defensive_rating": row[2],
            "pace": row[3],
            "opp_points_pg": row[4],
            "opp_fg_pct": row[5],
            "opp_three_pct": row[6],
            "record": f"{row[7]}-{row[8]}",
        }

    def get_active_injuries(self, team: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            cur = conn.cursor()
            if team:
                cur.execute(
                    """
                    SELECT player_name, team, injury_type, status, return_date
                    FROM injury_report
                    WHERE team = ? AND status IN ('Out','Doubtful','Questionable')
                    ORDER BY status
                    """,
                    (team,),
                )
            else:
                cur.execute(
                    """
                    SELECT player_name, team, injury_type, status, return_date
                    FROM injury_report
                    WHERE status IN ('Out','Doubtful','Questionable')
                    ORDER BY team
                    """
                )
            return [
                {"player": r[0], "team": r[1], "injury": r[2],
                 "status": r[3], "return_date": r[4]}
                for r in cur.fetchall()
            ]

    @staticmethod
    def _mean(values: List[float]) -> Optional[float]:
        return sum(values) / len(values) if values else None

    @staticmethod
    def _std(values: List[float]) -> Optional[float]:
        if len(values) < 2:
            return None
        m = sum(values) / len(values)
        var = sum((v - m) ** 2 for v in values) / (len(values) - 1)
        return sqrt(var)

    @staticmethod
    def _hit_rate(values: List[float], line: float, direction: str) -> Optional[float]:
        if not values:
            return None
        if direction == "over":
            hits = sum(1 for v in values if v > line)
        else:
            hits = sum(1 for v in values if v < line)
        return hits / len(values)

    def evaluate_line(
        self,
        player_name: str,
        stat: str,
        line: float,
        opponent: Optional[str] = None,
        direction: str = "over",
        american_odds: Optional[int] = None,
    ) -> LineEvaluation:
        """Evaluate a single prop line. Returns a LineEvaluation."""
        stat_key = normalize_stat(stat)
        stat_expr, stat_label = STAT_COLUMNS[stat_key]
        direction = direction.lower().strip()
        if direction not in ("over", "under"):
            raise ValueError("direction must be 'over' or 'under'")

        all_games = self._fetch_games(player_name, stat_expr)
        if not all_games:
            return LineEvaluation(
                player=player_name,
                stat=stat_key,
                stat_label=stat_label,
                line=line,
                direction=direction,
                sample_size=0,
                recent_sample_size=0,
                season_avg=None,
                recent_avg=None,
                vs_opponent_avg=None,
                home_avg=None,
                away_avg=None,
                std_dev=None,
                projection=None,
                hit_rate_season=None,
                hit_rate_recent=None,
                hit_rate_vs_opponent=None,
                prob_normal_model=None,
                blended_probability=None,
                edge_vs_line=None,
                edge_vs_implied=None,
                recommendation="NO DATA",
                confidence="low",
                warnings=[f"No game logs found for '{player_name}'."],
            )

        all_values = [g["value"] for g in all_games]
        recent_games = all_games[: self.RECENT_GAMES]
        recent_values = [g["value"] for g in recent_games]

        opp_games = (
            [g for g in all_games if opponent and g["opponent"] == opponent]
            if opponent
            else []
        )
        opp_values = [g["value"] for g in opp_games]

        home_values = [g["value"] for g in all_games if g["is_home"] is True]
        away_values = [g["value"] for g in all_games if g["is_home"] is False]

        season_avg = self._mean(all_values)
        recent_avg = self._mean(recent_values)
        opp_avg = self._mean(opp_values) if opp_values else None
        std = self._std(recent_values) or self._std(all_values)

        # Projection: use elite predictor for points if available, otherwise
        # weight recent form heavily.
        projection = None
        if self.predictor and stat_key == "points" and opponent:
            try:
                pred = self.predictor.elite_predict_performance(
                    player_name=player_name,
                    opponent=opponent,
                    game_date=datetime.now(),
                    is_home=True,
                    injury_status=None,
                )
                projection = (
                    pred.get("predicted_points")
                    or pred.get("base_prediction")
                    or pred.get("prediction")
                )
            except Exception:
                projection = None
        if projection is None:
            # 60% recent, 30% season, 10% vs-opponent (when available)
            parts = []
            if recent_avg is not None:
                parts.append((recent_avg, 0.6))
            if season_avg is not None:
                parts.append((season_avg, 0.3 if opp_avg is not None else 0.4))
            if opp_avg is not None:
                parts.append((opp_avg, 0.1))
            if parts:
                total_w = sum(w for _, w in parts)
                projection = sum(v * w for v, w in parts) / total_w

        # Empirical hit rates
        hr_season = self._hit_rate(all_values, line, direction)
        hr_recent = self._hit_rate(recent_values, line, direction)
        hr_opp = self._hit_rate(opp_values, line, direction) if opp_values else None

        # Normal-distribution probability around projection
        prob_normal = None
        if projection is not None and std and std > 0:
            p_over = 1.0 - normal_cdf(line, projection, std)
            prob_normal = p_over if direction == "over" else (1.0 - p_over)

        # Blend the signals
        components = []
        if hr_recent is not None:
            components.append((hr_recent, 0.4))
        if hr_season is not None:
            components.append((hr_season, 0.25))
        if hr_opp is not None and len(opp_values) >= 3:
            components.append((hr_opp, 0.15))
        if prob_normal is not None:
            components.append((prob_normal, 0.20))

        blended = None
        if components:
            total_w = sum(w for _, w in components)
            blended = sum(p * w for p, w in components) / total_w

        # Edge vs the implied line midpoint (assumes -110 fair = 0.5)
        edge_vs_line = (blended - 0.5) if blended is not None else None
        edge_vs_implied = None
        if blended is not None and american_odds is not None:
            edge_vs_implied = blended - implied_prob_from_american_odds(american_odds)

        # Recommendation
        rec, confidence = self._recommend(blended, len(all_values), len(recent_values))

        reasoning = self._build_reasoning(
            stat_label, line, direction, season_avg, recent_avg, opp_avg,
            projection, std, hr_season, hr_recent, hr_opp, prob_normal, blended,
        )

        warnings: List[str] = []
        if len(all_values) < self.MIN_SAMPLE:
            warnings.append(
                f"Small sample ({len(all_values)} games). Treat with caution."
            )
        if opponent and not opp_values:
            warnings.append(f"No prior matchups vs {opponent} in the database.")

        return LineEvaluation(
            player=player_name,
            stat=stat_key,
            stat_label=stat_label,
            line=line,
            direction=direction,
            sample_size=len(all_values),
            recent_sample_size=len(recent_values),
            season_avg=round(season_avg, 2) if season_avg is not None else None,
            recent_avg=round(recent_avg, 2) if recent_avg is not None else None,
            vs_opponent_avg=round(opp_avg, 2) if opp_avg is not None else None,
            home_avg=round(self._mean(home_values), 2) if home_values else None,
            away_avg=round(self._mean(away_values), 2) if away_values else None,
            std_dev=round(std, 2) if std else None,
            projection=round(projection, 2) if projection is not None else None,
            hit_rate_season=round(hr_season, 3) if hr_season is not None else None,
            hit_rate_recent=round(hr_recent, 3) if hr_recent is not None else None,
            hit_rate_vs_opponent=round(hr_opp, 3) if hr_opp is not None else None,
            prob_normal_model=round(prob_normal, 3) if prob_normal is not None else None,
            blended_probability=round(blended, 3) if blended is not None else None,
            edge_vs_line=round(edge_vs_line, 3) if edge_vs_line is not None else None,
            edge_vs_implied=round(edge_vs_implied, 3) if edge_vs_implied is not None else None,
            recommendation=rec,
            confidence=confidence,
            reasoning=reasoning,
            warnings=warnings,
        )

    @staticmethod
    def _recommend(blended: Optional[float], sample: int, recent: int) -> tuple:
        if blended is None:
            return ("INSUFFICIENT DATA", "low")
        if sample < 5 or recent < 3:
            return ("PASS — small sample", "low")
        if blended >= 0.65:
            return ("STRONG HIT", "high")
        if blended >= 0.575:
            return ("LEAN HIT", "medium")
        if blended <= 0.35:
            return ("STRONG MISS", "high")
        if blended <= 0.425:
            return ("LEAN MISS", "medium")
        return ("PASS — coinflip", "low")

    @staticmethod
    def _build_reasoning(
        stat_label, line, direction, season_avg, recent_avg, opp_avg,
        projection, std, hr_season, hr_recent, hr_opp, prob_normal, blended,
    ) -> List[str]:
        out: List[str] = []
        out.append(f"Line: {direction.upper()} {line} {stat_label}")
        if recent_avg is not None:
            out.append(f"Last-10 avg: {recent_avg:.2f} (line is {line})")
        if season_avg is not None:
            out.append(f"Season avg: {season_avg:.2f}")
        if opp_avg is not None:
            out.append(f"vs this opponent: {opp_avg:.2f} avg")
        if projection is not None:
            out.append(f"Projection: {projection:.2f}")
        if std is not None:
            out.append(f"Std dev (volatility): {std:.2f}")
        if hr_recent is not None:
            out.append(f"Hit rate last 10: {hr_recent:.0%}")
        if hr_season is not None:
            out.append(f"Hit rate season: {hr_season:.0%}")
        if hr_opp is not None:
            out.append(f"Hit rate vs opponent: {hr_opp:.0%}")
        if prob_normal is not None:
            out.append(f"Normal-model probability: {prob_normal:.0%}")
        if blended is not None:
            out.append(f"Blended {direction} probability: {blended:.0%}")
        return out

    def best_lines_for_player(
        self,
        player_name: str,
        opponent: Optional[str] = None,
        common_lines: Optional[Dict[str, List[float]]] = None,
    ) -> List[Dict[str, Any]]:
        """Score a grid of common lines and return the strongest opportunities."""
        if common_lines is None:
            # A reasonable default grid; the AI advisor can pass actual book lines.
            common_lines = {
                "points": [14.5, 17.5, 19.5, 22.5, 24.5, 27.5, 29.5, 32.5],
                "rebounds": [4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5],
                "assists": [3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5],
                "threes": [1.5, 2.5, 3.5, 4.5],
                "pra": [25.5, 30.5, 35.5, 40.5, 45.5],
            }

        results = []
        for stat, lines in common_lines.items():
            for line in lines:
                for direction in ("over", "under"):
                    try:
                        ev = self.evaluate_line(
                            player_name, stat, line, opponent, direction
                        )
                    except Exception:
                        continue
                    if ev.blended_probability is None:
                        continue
                    if ev.sample_size < self.MIN_SAMPLE:
                        continue
                    results.append({
                        "stat": ev.stat_label,
                        "direction": direction,
                        "line": line,
                        "probability": ev.blended_probability,
                        "edge": ev.edge_vs_line,
                        "recommendation": ev.recommendation,
                        "sample_size": ev.sample_size,
                    })

        results.sort(key=lambda r: abs(r["edge"] or 0), reverse=True)
        return results[:10]
