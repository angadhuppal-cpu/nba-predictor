import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

# Check total players with game history
cursor.execute("SELECT COUNT(DISTINCT player_name) FROM player_stats")
print(f'Players with game history: {cursor.fetchone()[0]}')

# Check Chris Paul in season stats
cursor.execute("SELECT player_name, games_played, points_avg, team FROM player_season_stats WHERE season = '2025-26' AND player_name LIKE '%Chris%Paul%'")
result = cursor.fetchone()

if result:
    print(f'\nChris Paul 2025-26 season stats:')
    print(f'  Name: {result[0]}')
    print(f'  Team: {result[3]}')
    print(f'  Games played: {result[1]}')
    print(f'  PPG: {result[2]}')
else:
    print('\nChris Paul NOT found in 2025-26 season stats')

# Check if he has any game logs from previous seasons
cursor.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM player_stats WHERE player_name LIKE '%Chris%Paul%'")
count, min_date, max_date = cursor.fetchone()
print(f'\nChris Paul historical game logs: {count}')
if count > 0:
    print(f'  Date range: {min_date} to {max_date}')

conn.close()
