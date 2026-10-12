"""Betting math: odds conversion, vig removal, expected value, Kelly sizing, parlays."""

from __future__ import annotations

import math
from dataclasses import dataclass


def american_to_decimal(odds: float) -> float:
    if odds == 0 or -100 < odds < 100:
        raise ValueError(f"Invalid American odds: {odds}")
    return 1 + (odds / 100 if odds > 0 else 100 / -odds)


def decimal_to_american(dec: float) -> int:
    if dec <= 1:
        raise ValueError(f"Decimal odds must be > 1, got {dec}")
    if dec >= 2:
        return round((dec - 1) * 100)
    return round(-100 / (dec - 1))


def american_to_implied(odds: float) -> float:
    """Implied probability including the bookmaker's vig."""
    return 1 / american_to_decimal(odds)


def prob_to_american(p: float) -> int:
    """Fair (no-vig) American odds for a win probability."""
    p = min(max(p, 1e-6), 1 - 1e-6)
    return decimal_to_american(1 / p)


def no_vig_probs(odds_a: float, odds_b: float) -> tuple[float, float]:
    """Strip the vig from a two-way market using proportional normalisation."""
    a, b = american_to_implied(odds_a), american_to_implied(odds_b)
    total = a + b
    return a / total, b / total


def expected_value(p_win: float, odds: float, p_push: float = 0.0) -> float:
    """Expected profit per 1 unit staked. Pushes return the stake."""
    profit = american_to_decimal(odds) - 1
    p_loss = 1 - p_win - p_push
    return p_win * profit - p_loss


def kelly_fraction(p_win: float, odds: float, p_push: float = 0.0) -> float:
    """Full-Kelly bankroll fraction (0 if no edge). Pushes are removed from the sample."""
    if p_push >= 1:
        return 0.0
    p = p_win / (1 - p_push)
    b = american_to_decimal(odds) - 1
    f = (b * p - (1 - p)) / b
    return max(f, 0.0)


@dataclass
class BetEvaluation:
    side: str
    odds: float
    model_prob: float
    push_prob: float
    implied_prob: float
    fair_market_prob: float | None
    edge: float
    ev_per_unit: float
    kelly_full: float

    def as_dict(self) -> dict:
        return {
            "side": self.side,
            "odds": self.odds,
            "model_win_prob": round(self.model_prob, 4),
            "push_prob": round(self.push_prob, 4),
            "book_implied_prob": round(self.implied_prob, 4),
            "no_vig_market_prob": None if self.fair_market_prob is None else round(self.fair_market_prob, 4),
            "edge_vs_market": round(self.edge, 4),
            "ev_per_1_unit": round(self.ev_per_unit, 4),
            "kelly_full_pct": round(100 * self.kelly_full, 2),
            "kelly_quarter_pct": round(25 * self.kelly_full, 2),
        }


def evaluate_bet(
    side: str,
    odds: float,
    model_prob: float,
    push_prob: float = 0.0,
    opposite_odds: float | None = None,
) -> BetEvaluation:
    implied = american_to_implied(odds)
    fair = no_vig_probs(odds, opposite_odds)[0] if opposite_odds is not None else None
    # Compare win probability conditional on no push with the market's view.
    cond_prob = model_prob / (1 - push_prob) if push_prob < 1 else 0.0
    edge = cond_prob - (fair if fair is not None else implied)
    return BetEvaluation(
        side=side,
        odds=odds,
        model_prob=model_prob,
        push_prob=push_prob,
        implied_prob=implied,
        fair_market_prob=fair,
        edge=edge,
        ev_per_unit=expected_value(model_prob, odds, push_prob),
        kelly_full=kelly_fraction(model_prob, odds, push_prob),
    )


def parlay(legs: list[dict]) -> dict:
    """Price a parlay assuming independent legs.

    Each leg: {"prob": model win probability, "odds": American odds (optional)}.
    """
    if not legs:
        raise ValueError("Parlay needs at least one leg")
    p = math.prod(leg["prob"] for leg in legs)
    out = {
        "legs": len(legs),
        "model_hit_prob": round(p, 4),
        "fair_american_odds": prob_to_american(p),
        "note": "Assumes legs are independent. Same-game legs are often correlated, so treat this as approximate.",
    }
    if all("odds" in leg and leg["odds"] is not None for leg in legs):
        dec = math.prod(american_to_decimal(leg["odds"]) for leg in legs)
        out["book_american_odds"] = decimal_to_american(dec)
        out["book_implied_prob"] = round(1 / dec, 4)
        out["ev_per_1_unit"] = round(p * (dec - 1) - (1 - p), 4)
    return out
