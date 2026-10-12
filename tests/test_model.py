import numpy as np
import pytest

from nba_predictor import model
from tests.conftest import make_games


def test_normalize_stat():
    assert model.normalize_stat("points") == "PTS"
    assert model.normalize_stat("pts+reb+ast") == "PRA"
    assert model.normalize_stat("3PM") == "FG3M"
    assert model.normalize_stat("Rebounds + Assists".replace(" ", "")) == "RA"
    with pytest.raises(ValueError):
        model.normalize_stat("dunks")


def test_projection_recovers_mean(games):
    p = model.project(games, "PTS")
    assert 22 < p.mean < 28
    assert 32 < p.minutes < 38
    assert p.distribution.sd > 3


def test_probabilities_sum_to_one(games):
    d = model.project(games, "REB").distribution
    for line in (6.5, 7, 7.5, 12):
        pr = d.probs(line)
        assert sum(pr.values()) == pytest.approx(1.0, abs=1e-9)
    assert d.probs(6.5)["push"] == 0
    assert d.probs(7)["push"] > 0


def test_probability_monotonic_in_line(games):
    d = model.project(games, "PTS").distribution
    overs = [d.probs(x + 0.5)["over"] for x in range(10, 40)]
    assert all(a >= b for a, b in zip(overs, overs[1:]))


def test_matchup_factor_direction(games, team_ctx):
    soft = model.project(games, "PTS", opponent="LAL", team_ctx=team_ctx)
    tough = model.project(games, "PTS", opponent="BOS", team_ctx=team_ctx)
    assert soft.mean > tough.mean
    assert soft.factors["matchup"] > 1 > tough.factors["matchup"]


def test_minutes_override_scales_projection(games):
    base = model.project(games, "PTS")
    more = model.project(games, "PTS", minutes_override=base.minutes * 1.2)
    assert more.mean == pytest.approx(base.mean * 1.2, rel=1e-6)


def test_combo_stat(games):
    pra = model.project(games, "PRA").mean
    parts = sum(model.project(games, s).mean for s in ("PTS", "REB", "AST"))
    assert pra == pytest.approx(parts, rel=1e-6)


def test_analyze_line_with_odds(games, team_ctx):
    r = model.analyze_line(games, "PTS", 18.5, over_odds=-110, under_odds=-110, opponent="LAL", team_ctx=team_ctx, home=True)
    assert r["verdict"]["pick"] == "OVER"
    assert r["verdict"]["strength"] == "STRONG"
    assert r["bet_evaluation"]["over"]["ev_per_1_unit"] > 0
    assert r["hit_rates"]["last_10"]["games"] == 10
    assert "vs_LAL" in r["hit_rates"]


def test_alt_lines(games):
    r = model.alt_lines(games, "PTS", offered=[{"line": 19.5, "side": "over", "odds": -200},
                                                {"line": 30.5, "side": "over", "odds": 250}])
    lines = [row["line"] for row in r["ladder"]]
    assert lines == sorted(lines)
    assert r["highest_over_line_with_70pct"]["p_over"] >= 0.70
    ranked = r["offered_lines_ranked_by_ev"]
    assert ranked[0]["ev_per_1_unit"] >= ranked[1]["ev_per_1_unit"]


def test_calibration_on_synthetic_player():
    """Over many simulated seasons the model's P(over) should match reality."""
    preds, outcomes = [], []
    for seed in range(40):
        g = make_games(n=41, seed=seed)
        nxt, hist = g.iloc[0], g.iloc[1:]
        p = model.project(hist, "PTS").distribution.probs(24.5)["over"]
        preds.append(p)
        outcomes.append(nxt["PTS"] > 24.5)
    brier = np.mean((np.array(preds) - np.array(outcomes, float)) ** 2)
    assert brier < 0.26


def test_backtest_runs(games):
    r = model.backtest(games, "PTS", n_tests=15)
    assert r["games_tested"] == 15
    assert 0 <= r["brier_score"] <= 1


def test_too_few_games():
    with pytest.raises(ValueError):
        model.project(make_games(n=2), "PTS")
