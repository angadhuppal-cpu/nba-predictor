"""
Fetch NBA data for 2025-26 season (current season)
"""
from nba_data_pipeline import NBADataPipeline
import sqlite3

season = '2025-26'

print("=" * 70)
print("FETCHING 2025-26 NBA SEASON DATA")
print("=" * 70)
print(f"Season: {season}")
print("=" * 70)

pipeline = NBADataPipeline()
pipeline.season = season

try:
    pipeline.connect_db()

    # Fetch player season stats
    print(f"\n[1/3] Fetching player season stats for {season}...")
    season_stats = pipeline.fetch_player_season_stats(season=season)

    if not season_stats.empty:
        cursor = pipeline.conn.cursor()

        for _, row in season_stats.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_season_stats
                    (player_id, player_name, team, season, games_played,
                     minutes_avg, points_avg, rebounds_avg, assists_avg,
                     steals_avg, blocks_avg, turnovers_avg,
                     field_goal_pct, three_point_pct, free_throw_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['PLAYER_ID']), row['PLAYER_NAME'], row['TEAM_ABBREVIATION'],
                    season, row.get('GP', 0),
                    row.get('MIN', 0), row.get('PTS', 0), row.get('REB', 0),
                    row.get('AST', 0), row.get('STL', 0), row.get('BLK', 0),
                    row.get('TOV', 0), row.get('FG_PCT', 0),
                    row.get('FG3_PCT', 0), row.get('FT_PCT', 0)
                ))
            except Exception as e:
                pass

        pipeline.conn.commit()
        print(f"  [OK] Saved {len(season_stats)} player season stats")
    else:
        print(f"  [WARNING] No player season stats found for {season}")

    # Fetch team stats
    print(f"\n[2/3] Fetching team stats for {season}...")
    team_stats = pipeline.fetch_team_stats(season=season)

    if not team_stats.empty:
        cursor = pipeline.conn.cursor()

        for _, row in team_stats.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO team_stats
                    (team_id, team_name, season, date, wins, losses,
                     offensive_rating, defensive_rating, net_rating, pace)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['TEAM_ID']), row['TEAM_NAME'], season,
                    f"{season.split('-')[0]}-12-31",
                    row.get('W', 0), row.get('L', 0),
                    row.get('OFF_RATING', 0), row.get('DEF_RATING', 0),
                    row.get('NET_RATING', 0), row.get('PACE', 0)
                ))
            except Exception as e:
                pass

        pipeline.conn.commit()
        print(f"  [OK] Saved {len(team_stats)} team stats")
    else:
        print(f"  [WARNING] No team stats found for {season}")

    # Fetch game logs for top 100 players by PPG in this season
    print(f"\n[3/3] Fetching game logs for top 100 players in {season}...")

    if not season_stats.empty:
        top_players = season_stats.nlargest(100, 'PTS')
        cursor = pipeline.conn.cursor()
        games_count = 0

        for idx, player in top_players.iterrows():
            player_id = str(player['PLAYER_ID'])
            player_name = player['PLAYER_NAME']
            team = player['TEAM_ABBREVIATION']

            try:
                print(f"  [{idx+1}/100] {player_name} ({player.get('PTS', 0):.1f} PPG)")
            except:
                print(f"  [{idx+1}/100] Player {player_id}")

            game_logs = pipeline.fetch_player_game_logs(player_id, season=season)

            if game_logs.empty:
                continue

            for _, game in game_logs.iterrows():
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO player_stats
                        (player_id, player_name, team, date, opponent, is_home,
                         minutes, points, rebounds, assists, steals, blocks, turnovers,
                         field_goals_made, field_goals_attempted,
                         three_pointers_made, three_pointers_attempted,
                         free_throws_made, free_throws_attempted, plus_minus)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        player_id, player_name, team,
                        game.get('GAME_DATE', ''),
                        game.get('MATCHUP', '').split()[-1] if game.get('MATCHUP') else '',
                        'vs' in game.get('MATCHUP', ''),
                        game.get('MIN', 0), game.get('PTS', 0), game.get('REB', 0),
                        game.get('AST', 0), game.get('STL', 0), game.get('BLK', 0),
                        game.get('TOV', 0), game.get('FGM', 0), game.get('FGA', 0),
                        game.get('FG3M', 0), game.get('FG3A', 0),
                        game.get('FTM', 0), game.get('FTA', 0), game.get('PLUS_MINUS', 0)
                    ))
                    games_count += 1
                except Exception as e:
                    pass

            if (idx + 1) % 10 == 0:
                pipeline.conn.commit()

        pipeline.conn.commit()
        print(f"  [OK] Saved {games_count} game records")

    pipeline.close_db()

    print(f"\n[OK] Completed {season}")

except Exception as e:
    print(f"[ERROR] Failed to fetch {season}: {e}")
    import traceback
    traceback.print_exc()
    if pipeline.conn:
        pipeline.close_db()

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM player_season_stats WHERE season = '2025-26'")
print(f"2025-26 player-season records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM player_stats WHERE date >= '2025-10-01'")
print(f"2025-26 game records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM team_stats WHERE season = '2025-26'")
print(f"2025-26 team-season records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(DISTINCT season) FROM player_season_stats")
print(f"Total seasons in database: {cursor.fetchone()[0]}")

conn.close()

print("=" * 70)
print("[OK] 2025-26 SEASON DATA FETCH COMPLETE!")
print("=" * 70)
