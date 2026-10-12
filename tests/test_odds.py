import pytest

from nba_predictor import odds


def test_conversions():
    assert odds.american_to_decimal(-110) == pytest.approx(1.9091, abs=1e-4)
    assert odds.american_to_decimal(150) == 2.5
    assert odds.american_to_implied(-110) == pytest.approx(0.5238, abs=1e-4)
    assert odds.prob_to_american(0.5) == 100
    assert odds.prob_to_american(0.75) == -300
    assert odds.prob_to_american(0.25) == 300


def test_no_vig():
    a, b = odds.no_vig_probs(-110, -110)
    assert a == pytest.approx(0.5) and b == pytest.approx(0.5)
    a, b = odds.no_vig_probs(-150, 130)
    assert a + b == pytest.approx(1.0) and a > b


def test_ev_and_kelly():
    assert odds.expected_value(0.5238, -110) == pytest.approx(0, abs=1e-3)
    assert odds.expected_value(0.60, -110) > 0
    assert odds.kelly_fraction(0.45, -110) == 0
    # 60% at even money: Kelly = 2p - 1 = 20%
    assert odds.kelly_fraction(0.60, 100) == pytest.approx(0.20)


def test_evaluate_bet_push_handling():
    ev = odds.evaluate_bet("OVER", -110, model_prob=0.5, push_prob=0.1, opposite_odds=-110)
    # conditional on no push the over wins 55.6% vs a 50% fair market
    assert ev.edge == pytest.approx(0.0556, abs=1e-3)


def test_parlay():
    p = odds.parlay([{"prob": 0.6, "odds": -110}, {"prob": 0.6, "odds": -110}])
    assert p["model_hit_prob"] == pytest.approx(0.36)
    assert p["book_american_odds"] == 264


def test_invalid_odds():
    with pytest.raises(ValueError):
        odds.american_to_decimal(50)
