#!/usr/bin/env python3
"""
Full refresh of every active 2025-26 player's game logs.

Differs from fetch_all_active_players_2025_26.py: that one skips players
who already have any game logs in the DB, which is fine for the initial
backfill but breaks incremental "give me the latest games" updates. This
one re-fetches every active player's full-season game log every time;
the pipeline upserts on (player_id, date) so duplicates aren't created
and only NEW rows actually land.

Usage:
    python update_all_players_games.py
    python update_all_players_games.py --season 2024-25
    python update_all_players_games.py --min-games 10
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from datetime import datetime

from nba_data_pipeline import NBADataPipeline


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="2025-26",
                    help="NBA season (e.g. 2025-26). Default: 2025-26.")
    ap.add_argument("--min-games", type=int, default=1,
                    help="Skip players with fewer than this many games in season_stats.")
    ap.add_argument("--sleep", type=float, default=0.6,
                    help="Seconds between API calls (NBA rate-limit cushion).")
    args = ap.parse_args()

    print("=" * 70)
    print(f"UPDATING GAME LOGS FOR ALL {args.season} ACTIVE PLAYERS")
    print(f"As of: {datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 70)

    pipeline = NBADataPipeline()
    pipeline.season = args.season
    pipeline.connect_db()

    cursor = pipeline.conn.cursor()
    cursor.execute(
        """
        SELECT player_id, player_name, team, games_played, points_avg
        FROM player_season_stats
        WHERE season = ? AND games_played >= ?
        ORDER BY points_avg DESC
        """,
        (args.season, args.min_games),
    )
    players = cursor.fetchall()
    total = len(players)
    if total == 0:
        print(f"\n[!] No players found for {args.season} with >= {args.min_games} games.")
        print(f"    Run populate_season_stats.py first to seed the player_season_stats table.")
        return 1

    print(f"\nFound {total} players. Re-fetching full-season game logs...")
    print("(Pipeline upserts on player_id+date; only new games actually land.)\n")

    new_rows_total = 0
    failed = 0
    start = time.time()

    for idx, (player_id, player_name, team, gp, ppg) in enumerate(players, 1):
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM player_stats WHERE player_id = ?",
                (player_id,),
            )
            before = cursor.fetchone()[0]

            game_logs = pipeline.fetch_player_game_logs(
                player_id, season=args.season
            )
            if game_logs is None or game_logs.empty:
                print(f"  [{idx}/{total}] {player_name:30s}  (no games returned)")
                continue

            # Use the pipeline's save method so column mapping/upsert logic
            # stays in one place.
            saved = _save_game_logs(pipeline, player_id, player_name, team, game_logs)
            cursor.execute(
                "SELECT COUNT(*) FROM player_stats WHERE player_id = ?",
                (player_id,),
            )
            after = cursor.fetchone()[0]
            new_rows = max(0, after - before)
            new_rows_total += new_rows

            mark = "+" if new_rows > 0 else "="
            print(
                f"  [{idx}/{total}] {player_name:30s}  "
                f"({ppg:5.1f} ppg, {gp:2d} gp) "
                f"{after:3d} games on file  {mark}{new_rows} new"
            )
        except Exception as exc:
            failed += 1
            print(f"  [{idx}/{total}] {player_name:30s}  ERROR: {exc}")
        finally:
            time.sleep(args.sleep)

    elapsed = time.time() - start
    print()
    print("=" * 70)
    print(f"Done in {elapsed/60:.1f} min. {new_rows_total} new game-log rows. {failed} failed.")
    print("=" * 70)
    return 0


def _save_game_logs(pipeline, player_id, player_name, team, df):
    """Best-effort save: try the pipeline's own helper, fall back to direct SQL."""
    save_fn = getattr(pipeline, "save_player_game_logs", None)
    if callable(save_fn):
        return save_fn(player_id, player_name, team, df)

    # Generic fallback — upsert by (player_id, date).
    cur = pipeline.conn.cursor()
    rows = 0
    for _, row in df.iterrows():
        try:
            game_date = str(row.get("GAME_DATE"))
            opponent = (row.get("MATCHUP") or "").split()[-1]
            is_home = "@" not in (row.get("MATCHUP") or "")
            cur.execute(
                """
                INSERT OR REPLACE INTO player_stats (
                    player_id, player_name, team, date, opponent, is_home,
                    minutes, points, rebounds, assists, steals, blocks,
                    turnovers, field_goals_made, field_goals_attempted,
                    three_pointers_made, three_pointers_attempted,
                    free_throws_made, free_throws_attempted, plus_minus,
                    fantasy_points, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    player_id, player_name, team, game_date, opponent, is_home,
                    row.get("MIN"), row.get("PTS"), row.get("REB"), row.get("AST"),
                    row.get("STL"), row.get("BLK"), row.get("TOV"),
                    row.get("FGM"), row.get("FGA"), row.get("FG3M"), row.get("FG3A"),
                    row.get("FTM"), row.get("FTA"), row.get("PLUS_MINUS"),
                    None,
                ),
            )
            rows += 1
        except Exception:
            continue
    pipeline.conn.commit()
    return rows


if __name__ == "__main__":
    sys.exit(main())
