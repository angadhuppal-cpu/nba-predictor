"""NBA data access via nba_api (stats.nba.com), with an on-disk cache.

stats.nba.com is slow and rate-limits aggressively, so every response is cached
under ~/.cache/nba_predictor (override with NBA_PREDICTOR_CACHE) for a few hours.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import time
import unicodedata
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(os.environ.get("NBA_PREDICTOR_CACHE", Path.home() / ".cache" / "nba_predictor"))
CACHE_TTL_SECONDS = 6 * 3600
REQUEST_PAUSE_SECONDS = 0.6  # be polite to stats.nba.com
REQUEST_TIMEOUT = 45

BOX_COLUMNS = ["PTS", "REB", "AST", "FG3M", "FG3A", "FGM", "FGA", "FTM", "FTA", "OREB", "DREB", "STL", "BLK", "TOV", "PF"]


class DataError(RuntimeError):
    pass


def current_season(today: dt.date | None = None) -> str:
    """NBA season string such as '2026-27'. Seasons roll over in October."""
    today = today or dt.date.today()
    start = today.year if today.month >= 10 else today.year - 1
    return f"{start}-{(start + 1) % 100:02d}"


def previous_season(season: str) -> str:
    start = int(season[:4]) - 1
    return f"{start}-{(start + 1) % 100:02d}"


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def find_player(name: str) -> dict:
    """Resolve a player name (accent/case-insensitive, partial OK) to nba_api's player dict."""
    from nba_api.stats.static import players

    query = _strip_accents(name).lower().strip()
    everyone = players.get_players()
    exact = [p for p in everyone if _strip_accents(p["full_name"]).lower() == query]
    matches = exact or [p for p in everyone if query in _strip_accents(p["full_name"]).lower()]
    if not matches:
        # Fall back to matching every word (e.g. "giannis" or "shai gilgeous").
        words = query.split()
        matches = [p for p in everyone if all(w in _strip_accents(p["full_name"]).lower() for w in words)]
    if not matches:
        raise DataError(f"No NBA player found matching '{name}'")
    matches.sort(key=lambda p: (not p["is_active"], len(p["full_name"])))
    return matches[0]


def find_team(name_or_abbr: str) -> dict:
    from nba_api.stats.static import teams

    q = name_or_abbr.strip().lower()
    for t in teams.get_teams():
        if q in (t["abbreviation"].lower(), t["nickname"].lower(), t["full_name"].lower(), t["city"].lower()):
            return t
    for t in teams.get_teams():
        if q in t["full_name"].lower():
            return t
    raise DataError(f"No NBA team found matching '{name_or_abbr}'")


def _cache_path(key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
    return CACHE_DIR / f"{safe}.json"


def _cached(key: str, fetch, ttl: int = CACHE_TTL_SECONDS) -> list[dict]:
    path = _cache_path(key)
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        return json.loads(path.read_text())
    try:
        records = fetch()
    except Exception as exc:  # network errors, timeouts, stats.nba.com blocking
        if path.exists():  # stale data beats no data
            return json.loads(path.read_text())
        print(f"[nba_predictor] fetching {key} failed: {exc}")
        raise DataError(
            "Couldn't load stats from NBA.com. The site is sometimes slow or briefly blocks requests: "
            "wait a minute and try again. If you're on a VPN or a work/school network, try turning it off."
        ) from exc
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records))
    time.sleep(REQUEST_PAUSE_SECONDS)
    return records


def _minutes(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    if isinstance(value, str) and ":" in value:
        m, s = value.split(":")[:2]
        return int(m) + int(s) / 60
    return float(value)


def _season_game_log(player_id: int, season: str, season_type: str) -> list[dict]:
    from nba_api.stats.endpoints import playergamelog

    def fetch():
        df = playergamelog.PlayerGameLog(
            player_id=player_id, season=season, season_type_all_star=season_type, timeout=REQUEST_TIMEOUT
        ).get_data_frames()[0]
        return df.to_dict("records")

    # Finished seasons never change, so cache them for a long time.
    ttl = CACHE_TTL_SECONDS if season == current_season() else 30 * 24 * 3600
    return _cached(f"gamelog_{player_id}_{season}_{season_type}", fetch, ttl)


def normalize_game_log(records: list[dict], season: str) -> pd.DataFrame:
    """Turn raw PlayerGameLog rows into a tidy frame the model understands."""
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="mixed")
    df["MIN"] = df["MIN"].map(_minutes)
    df["HOME"] = df["MATCHUP"].str.contains("vs.", regex=False)
    df["TEAM"] = df["MATCHUP"].str.split().str[0]
    df["OPP"] = df["MATCHUP"].str.split().str[-1]
    df["SEASON"] = season
    for col in BOX_COLUMNS:
        df[col] = pd.to_numeric(df.get(col), errors="coerce").fillna(0)
    keep = ["GAME_DATE", "SEASON", "MATCHUP", "TEAM", "OPP", "HOME", "WL", "MIN", *BOX_COLUMNS]
    return df[[c for c in keep if c in df.columns]]


def get_game_logs(player_name: str, seasons: list[str] | None = None, include_playoffs: bool = False) -> tuple[dict, pd.DataFrame]:
    """Game logs for a player across seasons, newest game first."""
    player = find_player(player_name)
    seasons = seasons or [current_season(), previous_season(current_season())]
    frames = []
    types = ["Regular Season"] + (["Playoffs"] if include_playoffs else [])
    for season in seasons:
        for season_type in types:
            frames.append(normalize_game_log(_season_game_log(player["id"], season, season_type), season))
    frames = [f for f in frames if not f.empty]
    if not frames:
        raise DataError(f"No game logs for {player['full_name']} in {', '.join(seasons)}")
    df = pd.concat(frames).sort_values("GAME_DATE", ascending=False).reset_index(drop=True)
    return player, df


def get_team_context(season: str | None = None) -> pd.DataFrame:
    """Per-team pace, defensive rating and per-game stats allowed to opponents.

    Index is the team abbreviation. Columns: PACE, DEF_RATING, OFF_RATING and
    OPP_<STAT> (points, rebounds, assists, threes... allowed per game).
    """
    from nba_api.stats.endpoints import leaguedashteamstats
    from nba_api.stats.static import teams

    season = season or current_season()

    def fetch(measure):
        def _f():
            df = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                measure_type_detailed_defense=measure,
                per_mode_detailed="PerGame",
                timeout=REQUEST_TIMEOUT,
            ).get_data_frames()[0]
            return df.to_dict("records")

        return _f

    adv = pd.DataFrame(_cached(f"teams_advanced_{season}", fetch("Advanced")))
    opp = pd.DataFrame(_cached(f"teams_opponent_{season}", fetch("Opponent")))
    if adv.empty or opp.empty:
        raise DataError(f"No team stats available yet for {season}")
    abbr = {t["id"]: t["abbreviation"] for t in teams.get_teams()}
    adv["ABBR"] = adv["TEAM_ID"].map(abbr)
    opp["ABBR"] = opp["TEAM_ID"].map(abbr)
    opp_cols = [c for c in opp.columns if c.startswith("OPP_")]
    adv_cols = [c for c in ["TEAM_NAME", "GP", "W", "L", "PACE", "OFF_RATING", "DEF_RATING", "NET_RATING"] if c in adv.columns]
    out = adv.set_index("ABBR")[adv_cols].join(
        opp.set_index("ABBR")[opp_cols]
    )
    return out
