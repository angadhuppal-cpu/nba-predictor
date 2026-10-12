import numpy as np
import pandas as pd
import pytest

TEAMS = ["BOS", "NYK", "MIA", "LAL", "DEN", "PHX", "GSW", "MIL"]


def make_games(n=60, pts=25.0, reb=7.0, ast=5.0, minutes=35.0, seed=0, season="2026-27"):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        m = max(0.0, rng.normal(minutes, 3))
        scale = m / minutes
        opp = TEAMS[i % len(TEAMS)]
        home = i % 2 == 0
        rows.append({
            "GAME_DATE": pd.Timestamp("2027-03-01") - pd.Timedelta(days=2 * i),
            "SEASON": season if i < n // 2 else "2025-26",
            "MATCHUP": f"XXX {'vs.' if home else '@'} {opp}",
            "TEAM": "XXX", "OPP": opp, "HOME": home, "WL": "W", "MIN": m,
            "PTS": rng.negative_binomial(pts * scale / 1.2, 1 / 2.2) if pts else 0,
            "REB": rng.poisson(reb * scale), "AST": rng.poisson(ast * scale),
            "FG3M": rng.poisson(2.5 * scale), "STL": rng.poisson(1.1 * scale), "BLK": rng.poisson(0.6 * scale),
            "TOV": rng.poisson(2.8 * scale), "FTM": rng.poisson(5 * scale), "FGM": rng.poisson(9 * scale),
            "FGA": rng.poisson(19 * scale), "FTA": rng.poisson(6 * scale), "FG3A": rng.poisson(7 * scale),
            "OREB": rng.poisson(1 * scale), "DREB": rng.poisson(6 * scale), "PF": rng.poisson(2),
        })
    return pd.DataFrame(rows)


@pytest.fixture
def games():
    return make_games()


@pytest.fixture
def team_ctx():
    df = pd.DataFrame({
        "TEAM_NAME": TEAMS, "PACE": [98, 100, 96, 101, 99, 100, 102, 97],
        "DEF_RATING": [108, 112, 110, 116, 114, 113, 115, 111],
        "OPP_PTS": [106, 112, 108, 120, 114, 113, 118, 110],
        "OPP_REB": [42, 44, 43, 46, 44, 44, 45, 43],
        "OPP_AST": [24, 25, 24, 28, 26, 26, 27, 25],
        "OPP_FG3M": [12, 13, 12, 15, 13, 13, 14, 12],
    }, index=TEAMS)
    return df
