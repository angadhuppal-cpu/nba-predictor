"""
Fetch game logs for ALL active players in 2025-26 season (10+ games played)
"""
from nba_data_pipeline import NBADataPipeline
import sqlite3

season = '2025-26'

print("=" * 70)
print("FETCHING GAME LOGS FOR ALL ACTIVE 2025-26 PLAYERS")
print("=" * 70)

pipeline = NBADataPipeline()
pipeline.season = season

try:
    pipeline.connect_db()

    # Get all players with 5+ games in current season
    cursor = pipeline.conn.cursor()
    cursor.execute("""
        SELECT player_id, player_name, team, games_played, points_avg
        FROM player_season_stats
        WHERE season = '2025-26' AND games_played >= 5
        ORDER BY player_name
    """)

    players = cursor.fetchall()
    total_players = len(players)
    print(f"\nFound {total_players} active players with 5+ games")
    print(f"Fetching game logs for all players...\n")

    games_count = 0
    players_with_games = 0

    for idx, (player_id, player_name, team, gp, ppg) in enumerate(players, 1):
        # Check if we already have game logs for this player
        cursor.execute("""
            SELECT COUNT(*) FROM player_stats
            WHERE player_id = ? AND date >= '2025-10-01'
        """, (player_id,))

        existing_games = cursor.fetchone()[0]

        if existing_games > 0:
            print(f"  [{idx}/{total_players}] {player_name:30s} - Already have {existing_games} games, skipping")
            players_with_games += 1
            games_count += existing_games
            continue

        try:
            print(f"  [{idx}/{total_players}] {player_name:30s} ({ppg:.1f} PPG, {gp} GP)")
        except:
            print(f"  [{idx}/{total_players}] Player {player_id}")

        game_logs = pipeline.fetch_player_game_logs(player_id, season=season)

        if game_logs.empty:
            continue

        player_games = 0
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
                player_games += 1
            except Exception as e:
                pass

        if player_games > 0:
            players_with_games += 1
            games_count += player_games

        if (idx) % 10 == 0:
            pipeline.conn.commit()
            print(f"    [Progress: {idx}/{total_players} players, {games_count} total games]")

    pipeline.conn.commit()
    pipeline.close_db()

    print(f"\n[OK] Completed fetching game logs")
    print(f"  Players processed: {total_players}")
    print(f"  Players with games: {players_with_games}")
    print(f"  Total games added: {games_count}")

except Exception as e:
    print(f"[ERROR] Failed: {e}")
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

cursor.execute("SELECT COUNT(DISTINCT player_name) FROM player_stats")
print(f"Total players with game history: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM player_stats WHERE date >= '2025-10-01'")
print(f"2025-26 game records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM player_stats")
print(f"All-time game records: {cursor.fetchone()[0]}")

# Check Chris Paul specifically
cursor.execute("SELECT COUNT(*) FROM player_stats WHERE player_name = 'Chris Paul'")
cp_games = cursor.fetchone()[0]
print(f"\nChris Paul game logs: {cp_games}")

conn.close()

print("=" * 70)
print("[OK] ALL ACTIVE PLAYERS GAME LOGS FETCHED!")
print("=" * 70)
