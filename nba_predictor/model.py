"""Statistical projection model for NBA player props.

How a projection is built:

1. Per-minute production for each box-score component, from recency-weighted
   game logs (exponential decay, last season down-weighted).
2. Projected minutes from a recency-weighted average of recent minutes, or a
   user override (injuries, rotation changes, blowout risk).
3. Matchup adjustment: how much the opponent allows of that stat per game
   relative to league average, shrunk halfway toward neutral so one soft
   defence doesn't swamp the player's own baseline.
4. Small home/away and back-to-back adjustments.
5. The outcome is modelled as a negative binomial (discrete, over-dispersed
   count distribution) whose variance comes from the player's own game-to-game
   spread, shrunk toward stat-typical priors, plus a term for uncertainty in the
   mean itself. That gives P(over), P(under) and P(push) for any line.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats as sps

from . import odds as oddsmath

STAT_COMPONENTS: dict[str, list[str]] = {
    "PTS": ["PTS"],
    "REB": ["REB"],
    "AST": ["AST"],
    "FG3M": ["FG3M"],
    "STL": ["STL"],
    "BLK": ["BLK"],
    "TOV": ["TOV"],
    "FTM": ["FTM"],
    "FGM": ["FGM"],
    "OREB": ["OREB"],
    "DREB": ["DREB"],
    "PRA": ["PTS", "REB", "AST"],
    "PR": ["PTS", "REB"],
    "PA": ["PTS", "AST"],
    "RA": ["REB", "AST"],
    "STOCKS": ["STL", "BLK"],
}

STAT_ALIASES = {
    "POINTS": "PTS", "PT": "PTS", "P": "PTS",
    "REBOUNDS": "REB", "REBS": "REB", "R": "REB",
    "ASSISTS": "AST", "ASTS": "AST", "A": "AST",
    "THREES": "FG3M", "3PM": "FG3M", "3PT": "FG3M", "3S": "FG3M", "3": "FG3M", "THREE_POINTERS": "FG3M", "3PTM": "FG3M",
    "STEALS": "STL", "BLOCKS": "BLK", "TURNOVERS": "TOV", "TO": "TOV",
    "PTS+REB+AST": "PRA", "P+R+A": "PRA", "PTSREBAST": "PRA",
    "PTS+REB": "PR", "P+R": "PR", "POINTS+REBOUNDS": "PR",
    "PTS+AST": "PA", "P+A": "PA", "POINTS+ASSISTS": "PA",
    "REB+AST": "RA", "R+A": "RA", "REBOUNDS+ASSISTS": "RA",
    "STL+BLK": "STOCKS", "S+B": "STOCKS", "BLK+STL": "STOCKS",
    "FREE_THROWS": "FTM", "FREE_THROWS_MADE": "FTM",
}

# Typical variance/mean ratio for each stat, used as a prior for over-dispersion.
DISPERSION_PRIOR = {
    "PTS": 2.2, "REB": 1.4, "AST": 1.5, "FG3M": 1.3, "STL": 1.1, "BLK": 1.4, "TOV": 1.2,
    "FTM": 1.6, "FGM": 1.3, "OREB": 1.3, "DREB": 1.3,
    "PRA": 2.8, "PR": 2.5, "PA": 2.5, "RA": 1.7, "STOCKS": 1.2,
}

OPP_COLUMN = {
    "PTS": "OPP_PTS", "REB": "OPP_REB", "AST": "OPP_AST", "FG3M": "OPP_FG3M", "STL": "OPP_STL",
    "BLK": "OPP_BLK", "TOV": "OPP_TOV", "FTM": "OPP_FTM", "FGM": "OPP_FGM", "OREB": "OPP_OREB", "DREB": "OPP_DREB",
}

RATE_HALF_LIFE_GAMES = 15  # recency weighting for per-minute production
MINUTES_HALF_LIFE_GAMES = 5  # minutes react faster to role changes
PRIOR_SEASON_WEIGHT = 0.6  # last season's games count less than this season's
MATCHUP_SHRINK = 0.5  # keep 50% of the opponent's deviation from league average
DISPERSION_PRIOR_GAMES = 20  # pseudo-games of weight given to the dispersion prior
HOME_FACTOR, AWAY_FACTOR = 1.012, 0.988
BACK_TO_BACK_MINUTES = 0.96
MIN_GAME_MINUTES = 6  # ignore cameo/injury-exit games when learning rates


def normalize_stat(stat: str) -> str:
    key = stat.strip().upper().replace(" ", "_").replace("-", "_")
    key = STAT_ALIASES.get(key, STAT_ALIASES.get(key.replace("_", "+"), key))
    if key not in STAT_COMPONENTS:
        raise ValueError(f"Unsupported stat '{stat}'. Supported: {', '.join(STAT_COMPONENTS)}")
    return key


def stat_series(df: pd.DataFrame, stat: str) -> pd.Series:
    return df[STAT_COMPONENTS[stat]].sum(axis=1)


def _recency_weights(df: pd.DataFrame, half_life: float) -> np.ndarray:
    """Exponential decay by game order (df is newest-first), last season discounted."""
    idx = np.arange(len(df))
    w = 0.5 ** (idx / half_life)
    if "SEASON" in df.columns and len(df):
        newest = df["SEASON"].iloc[0]
        w = w * np.where(df["SEASON"].to_numpy() == newest, 1.0, PRIOR_SEASON_WEIGHT)
    return w


def _weighted_var(x: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    mean = float(np.average(x, weights=w))
    var = float(np.average((x - mean) ** 2, weights=w))
    n_eff = w.sum() ** 2 / (w**2).sum()
    if n_eff > 1:
        var *= n_eff / (n_eff - 1)  # bias correction
    return mean, var


@dataclass
class Distribution:
    mean: float
    var: float

    def _nb(self):
        var = max(self.var, self.mean * 1.0001)
        p = self.mean / var
        n = self.mean**2 / (var - self.mean)
        return sps.nbinom(n, p)

    def probs(self, line: float) -> dict[str, float]:
        """P(over), P(under), P(push) for a line. Half-point lines can't push."""
        if self.mean <= 0:
            return {"over": 0.0, "under": 1.0, "push": 0.0}
        d = self._nb()
        if float(line).is_integer():
            k = int(line)
            push = float(d.pmf(k))
            under = float(d.cdf(k - 1))
            return {"over": max(0.0, 1 - under - push), "under": under, "push": push}
        under = float(d.cdf(int(np.floor(line))))
        return {"over": 1 - under, "under": under, "push": 0.0}

    def quantile(self, q: float) -> float:
        return float(self._nb().ppf(q)) if self.mean > 0 else 0.0

    @property
    def sd(self) -> float:
        return float(np.sqrt(self.var))


@dataclass
class Projection:
    stat: str
    mean: float
    distribution: Distribution
    minutes: float
    per_minute_rate: float
    baseline_mean: float  # before matchup/venue adjustments
    factors: dict[str, float] = field(default_factory=dict)
    sample_games: int = 0
    notes: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "stat": self.stat,
            "projected_mean": round(self.mean, 2),
            "projected_median": self.distribution.quantile(0.5),
            "std_dev": round(self.distribution.sd, 2),
            "range_25_75": [self.distribution.quantile(0.25), self.distribution.quantile(0.75)],
            "range_10_90": [self.distribution.quantile(0.10), self.distribution.quantile(0.90)],
            "projected_minutes": round(self.minutes, 1),
            "per_36": round(self.per_minute_rate * 36, 2),
            "baseline_before_adjustments": round(self.baseline_mean, 2),
            "adjustment_factors": {k: round(v, 3) for k, v in self.factors.items()},
            "games_in_sample": self.sample_games,
            "notes": self.notes,
        }


def matchup_factor(stat: str, opponent: str, team_ctx: pd.DataFrame | None, comp_means: dict[str, float]) -> tuple[float, str | None]:
    """How generous the opponent is with this stat relative to league average (shrunk)."""
    if team_ctx is None or opponent is None or opponent not in team_ctx.index:
        return 1.0, None
    num = den = 0.0
    for comp in STAT_COMPONENTS[stat]:
        col = OPP_COLUMN.get(comp)
        if col is None or col not in team_ctx.columns:
            continue
        league = team_ctx[col].mean()
        if league <= 0:
            continue
        ratio = team_ctx.loc[opponent, col] / league
        weight = max(comp_means.get(comp, 0.0), 1e-6)
        num += weight * ratio
        den += weight
    if den == 0:
        return 1.0, None
    raw = num / den
    factor = 1 + MATCHUP_SHRINK * (raw - 1)
    pct = 100 * (raw - 1)
    note = f"{opponent} allow {abs(pct):.1f}% {'more' if pct > 0 else 'less'} {stat} than league average"
    return factor, note


def project(
    games: pd.DataFrame,
    stat: str,
    opponent: str | None = None,
    home: bool | None = None,
    team_ctx: pd.DataFrame | None = None,
    minutes_override: float | None = None,
    back_to_back: bool = False,
    max_games: int = 82,
) -> Projection:
    """Project a player's stat distribution for the next game. `games` is newest-first."""
    stat = normalize_stat(stat)
    played = games[games["MIN"] >= MIN_GAME_MINUTES].head(max_games)
    if len(played) < 3:
        raise ValueError(f"Only {len(played)} usable games; need at least 3 to project")
    notes: list[str] = []

    w_rate = _recency_weights(played, RATE_HALF_LIFE_GAMES)
    mins = played["MIN"].to_numpy(float)
    comp_rates = {
        comp: float(np.sum(w_rate * played[comp].to_numpy(float)) / np.sum(w_rate * mins))
        for comp in STAT_COMPONENTS[stat]
    }
    rate = sum(comp_rates.values())

    if minutes_override is not None:
        minutes = float(minutes_override)
        notes.append(f"Minutes overridden to {minutes:.1f}")
    else:
        recent = played.head(15)
        minutes = float(np.average(recent["MIN"], weights=_recency_weights(recent, MINUTES_HALF_LIFE_GAMES)))
    factors: dict[str, float] = {}
    if back_to_back:
        minutes *= BACK_TO_BACK_MINUTES
        factors["back_to_back_minutes"] = BACK_TO_BACK_MINUTES
        notes.append("Back-to-back: minutes trimmed 4%")

    baseline = rate * minutes
    comp_means = {c: r * minutes for c, r in comp_rates.items()}

    m_factor, m_note = matchup_factor(stat, opponent, team_ctx, comp_means)
    if m_note:
        factors["matchup"] = m_factor
        notes.append(m_note)
    if home is not None:
        factors["venue"] = HOME_FACTOR if home else AWAY_FACTOR
    mean = baseline * float(np.prod([v for k, v in factors.items() if k != "back_to_back_minutes"]))

    # Over-dispersion from the player's own games, scaled to a per-minute basis
    # so a recent minutes change doesn't distort it, then shrunk toward a prior.
    values = stat_series(played, stat).to_numpy(float)
    scaled = values * (minutes / np.maximum(mins, 1))
    emp_mean, emp_var = _weighted_var(scaled, w_rate)
    emp_disp = emp_var / emp_mean if emp_mean > 0 else DISPERSION_PRIOR[stat]
    n_eff = w_rate.sum() ** 2 / (w_rate**2).sum()
    prior = DISPERSION_PRIOR[stat]
    disp = (n_eff * emp_disp + DISPERSION_PRIOR_GAMES * prior) / (n_eff + DISPERSION_PRIOR_GAMES)
    # Minutes uncertainty: the per-minute scaling above removes it, so add it back.
    min_cv = float(np.std(played.head(15)["MIN"]) / max(minutes, 1))
    if minutes_override is not None:
        min_cv = max(min_cv, 0.12)  # an override is a guess
    mean_uncertainty = (mean * 0.06) ** 2 + (mean * min_cv) ** 2 * 0.5
    var = max(disp, 1.02) * mean + mean_uncertainty

    if n_eff < 8:
        notes.append(f"Small sample (~{n_eff:.0f} effective games): treat with caution")
    if min_cv > 0.2:
        notes.append(f"Volatile minutes (CV {min_cv:.0%}): role is unsettled")

    return Projection(
        stat=stat,
        mean=mean,
        distribution=Distribution(mean=mean, var=var),
        minutes=minutes,
        per_minute_rate=rate,
        baseline_mean=baseline,
        factors=factors,
        sample_games=len(played),
        notes=notes,
    )


def hit_rates(games: pd.DataFrame, stat: str, line: float, opponent: str | None = None) -> dict:
    """How often the player actually cleared this line, over several windows."""
    stat = normalize_stat(stat)
    played = games[games["MIN"] > 0]
    vals = stat_series(played, stat)

    def rate(s: pd.Series) -> dict | None:
        if s.empty:
            return None
        over = int((s > line).sum())
        under = int((s < line).sum())
        return {"over": over, "under": under, "push": len(s) - over - under, "games": len(s),
                "over_pct": round(100 * over / len(s), 1), "avg": round(float(s.mean()), 2)}

    out = {f"last_{n}": rate(vals.head(n)) for n in (5, 10, 20)}
    if len(played):
        newest = played["SEASON"].iloc[0]
        out["this_season"] = rate(vals[played["SEASON"] == newest])
        out["all_loaded_games"] = rate(vals)
    if opponent:
        out[f"vs_{opponent}"] = rate(vals[played["OPP"] == opponent])
    out["recent_values"] = [int(v) for v in vals.head(10)]
    return out


def verdict(p_over: float, p_under: float, eval_over: dict | None = None, eval_under: dict | None = None) -> dict:
    """Turn probabilities (and edges, if odds were supplied) into a call."""
    side = "OVER" if p_over >= p_under else "UNDER"
    p = max(p_over, p_under)
    ev = eval_over if side == "OVER" else eval_under
    if ev is not None:
        edge = ev["edge_vs_market"]
        if edge >= 0.06:
            strength = "STRONG"
        elif edge >= 0.03:
            strength = "LEAN"
        elif edge > 0:
            strength = "SLIGHT EDGE (thin)"
        else:
            strength = "NO BET (no edge vs. the price)"
        basis = f"edge {edge:+.1%} vs. no-vig market"
    else:
        if p >= 0.62:
            strength = "STRONG"
        elif p >= 0.56:
            strength = "LEAN"
        else:
            strength = "COIN FLIP / PASS"
        basis = "probability only (no odds supplied; -110 needs 52.4% to break even)"
    return {"pick": side, "hit_probability": round(p, 4), "strength": strength, "basis": basis}


def analyze_line(
    games: pd.DataFrame,
    stat: str,
    line: float,
    over_odds: float | None = None,
    under_odds: float | None = None,
    **project_kwargs,
) -> dict:
    proj = project(games, stat, **project_kwargs)
    pr = proj.distribution.probs(line)
    eval_over = eval_under = None
    if over_odds is not None:
        eval_over = oddsmath.evaluate_bet("OVER", over_odds, pr["over"], pr["push"], under_odds).as_dict()
    if under_odds is not None:
        eval_under = oddsmath.evaluate_bet("UNDER", under_odds, pr["under"], pr["push"], over_odds).as_dict()
    return {
        "line": line,
        "projection": proj.summary(),
        "probabilities": {k: round(v, 4) for k, v in pr.items()},
        "fair_odds": {
            "over": oddsmath.prob_to_american(pr["over"] / (1 - pr["push"]) if pr["push"] < 1 else 0),
            "under": oddsmath.prob_to_american(pr["under"] / (1 - pr["push"]) if pr["push"] < 1 else 0),
        },
        "bet_evaluation": {"over": eval_over, "under": eval_under},
        "verdict": verdict(pr["over"], pr["under"], eval_over, eval_under),
        "hit_rates": hit_rates(games, stat, line, project_kwargs.get("opponent")),
    }


def alt_lines(
    games: pd.DataFrame,
    stat: str,
    offered: list[dict] | None = None,
    min_prob: float = 0.70,
    **project_kwargs,
) -> dict:
    """Probability ladder across alternate lines, plus best value if alt odds are given.

    offered: optional [{"line": 22.5, "side": "over", "odds": -150}, ...]
    """
    proj = project(games, stat, **project_kwargs)
    d = proj.distribution
    lo = max(0.5, np.floor(d.quantile(0.05)) - 0.5)
    hi = np.ceil(d.quantile(0.95)) + 0.5
    ladder = []
    for line in np.arange(lo, hi + 0.01, 1.0):
        pr = d.probs(float(line))
        ladder.append({
            "line": float(line),
            "p_over": round(pr["over"], 4),
            "p_under": round(pr["under"], 4),
            "fair_over_odds": oddsmath.prob_to_american(pr["over"]),
            "fair_under_odds": oddsmath.prob_to_american(pr["under"]),
        })
    safest_over = [r for r in ladder if r["p_over"] >= min_prob]
    safest_under = [r for r in ladder if r["p_under"] >= min_prob]
    out = {
        "projection": proj.summary(),
        "ladder": ladder,
        f"highest_over_line_with_{int(min_prob * 100)}pct": safest_over[-1] if safest_over else None,
        f"lowest_under_line_with_{int(min_prob * 100)}pct": safest_under[0] if safest_under else None,
    }
    if offered:
        rated = []
        for o in offered:
            side = o["side"].lower()
            pr = d.probs(float(o["line"]))
            ev = oddsmath.evaluate_bet(side.upper(), o["odds"], pr[side], pr["push"]).as_dict()
            rated.append({"line": o["line"], **ev})
        rated.sort(key=lambda r: r["ev_per_1_unit"], reverse=True)
        out["offered_lines_ranked_by_ev"] = rated
    return out


def backtest(games: pd.DataFrame, stat: str, n_tests: int = 30, min_history: int = 10) -> dict:
    """Walk-forward check: predict each recent game using only earlier games.

    A synthetic 'book line' is the player's prior 10-game average rounded to x.5,
    which is roughly how sportsbooks anchor lines. Reports calibration (Brier score,
    lower is better; always guessing 50% scores 0.25) and the hit rate of the
    model's picks overall and when it was confident.
    """
    stat = normalize_stat(stat)
    games = games[games["MIN"] > 0].reset_index(drop=True)
    rows = []
    for i in range(min(n_tests, len(games) - min_history)):
        history = games.iloc[i + 1 :]
        if len(history[history["MIN"] >= MIN_GAME_MINUTES]) < min_history:
            break
        actual = float(stat_series(games.iloc[[i]], stat).iloc[0])
        line = np.floor(stat_series(history.head(10), stat).mean()) + 0.5
        pr = project(history, stat, opponent=None).distribution.probs(line)
        went_over = actual > line
        pick_over = pr["over"] >= 0.5
        rows.append({"p_over": pr["over"], "over": went_over, "correct": pick_over == went_over,
                     "conf": max(pr["over"], pr["under"])})
    if not rows:
        return {"error": "Not enough games to backtest"}
    df = pd.DataFrame(rows)
    brier = float(((df["p_over"] - df["over"].astype(float)) ** 2).mean())
    confident = df[df["conf"] >= 0.58]
    return {
        "stat": stat,
        "games_tested": len(df),
        "brier_score": round(brier, 4),
        "brier_coinflip_baseline": 0.25,
        "pick_accuracy": round(float(df["correct"].mean()), 3),
        "confident_picks": len(confident),
        "confident_pick_accuracy": round(float(confident["correct"].mean()), 3) if len(confident) else None,
        "caveat": "Small samples are noisy; this is a sanity check, not proof of profitability.",
    }
