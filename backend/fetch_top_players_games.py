"""
Fetch game logs for top players by PPG
"""
from nba_data_pipeline import NBADataPipeline
import sqlite3
import sys

# Get top players by PPG
conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT player_id, player_name, team, points_avg
    FROM player_season_stats
    WHERE games_played >= 10
    ORDER BY points_avg DESC
    LIMIT 100
""")

top_players = cursor.fetchall()
conn.close()

print(f"Fetching game logs for top {len(top_players)} scorers...")
print("=" * 70)

# Create pipeline instance
pipeline = NBADataPipeline()
pipeline.connect_db()

cursor = pipeline.conn.cursor()
count = 0

for player_id, player_name, team, ppg in top_players:
    try:
        print(f"[{count+1}/100] {player_name} ({team}) - {ppg:.1f} PPG")
    except:
        print(f"[{count+1}/100] Player {player_id} - {ppg:.1f} PPG")

    # Fetch game logs
    game_logs = pipeline.fetch_player_game_logs(str(player_id))

    if game_logs.empty:
        print(f"  No games found")
        continue

    # Save to database
    games_added = 0
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
                str(player_id), player_name, team,
                game.get('GAME_DATE', ''),
                game.get('MATCHUP', '').split()[-1] if game.get('MATCHUP') else '',
                'vs' in game.get('MATCHUP', ''),
                game.get('MIN', 0), game.get('PTS', 0), game.get('REB', 0),
                game.get('AST', 0), game.get('STL', 0), game.get('BLK', 0),
                game.get('TOV', 0), game.get('FGM', 0), game.get('FGA', 0),
                game.get('FG3M', 0), game.get('FG3A', 0),
                game.get('FTM', 0), game.get('FTA', 0), game.get('PLUS_MINUS', 0)
            ))
            games_added += 1
        except Exception as e:
            pass

    pipeline.conn.commit()
    print(f"  Added {games_added} games")
    count += 1

pipeline.close_db()

print("\n" + "=" * 70)
print(f"[OK] Completed fetching game logs for {count} players")
