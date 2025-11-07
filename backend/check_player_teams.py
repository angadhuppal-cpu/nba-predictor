import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

# Check some notable players and their teams across seasons
notable_players = [
    'LeBron James', 'Kevin Durant', 'James Harden', 'Paul George',
    'Damian Lillard', 'Bradley Beal', 'Kristaps Porzingis'
]

for player in notable_players:
    cursor.execute("""
        SELECT season, team
        FROM player_season_stats
        WHERE player_name = ?
        ORDER BY season
    """, (player,))

    results = cursor.fetchall()
    if results:
        print(f"\n{player}:")
        for season, team in results:
            print(f"  {season}: {team}")

# Check what the backend cache sees (current season only)
print("\n" + "="*60)
print("Current season (2024-25) team assignments:")
print("="*60)

cursor.execute("""
    SELECT player_name, team, points_avg
    FROM player_season_stats
    WHERE season = '2024-25'
    ORDER BY points_avg DESC
    LIMIT 20
""")

for name, team, ppg in cursor.fetchall():
    print(f"{name:30s} {team:5s} {ppg:5.1f} PPG")

conn.close()
