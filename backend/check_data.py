import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

# Check which players have game data
cursor.execute("SELECT COUNT(DISTINCT player_name) FROM player_stats")
print(f"Players with game data: {cursor.fetchone()[0]}")

# List some players with game history
cursor.execute("SELECT DISTINCT player_name FROM player_stats ORDER BY player_name LIMIT 30")
print("\nPlayers with game history:")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# Check opponent format
cursor.execute("SELECT DISTINCT opponent FROM player_stats ORDER BY opponent")
opponents = [row[0] for row in cursor.fetchall()]
print(f"\nOpponent format: {opponents[:10]}")

conn.close()
