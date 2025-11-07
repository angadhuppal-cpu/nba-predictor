import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT season, COUNT(*) as players, AVG(points_avg) as avg_ppg
    FROM player_season_stats
    GROUP BY season
    ORDER BY season
""")

print('Season Statistics:')
print('-' * 60)
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]:3d} players, Avg PPG: {row[2]:.1f}')

print('-' * 60)

cursor.execute("""
    SELECT COUNT(*) as total_games,
           MIN(date) as earliest_game,
           MAX(date) as latest_game
    FROM player_stats
""")

row = cursor.fetchone()
print(f'\nGame Records: {row[0]:,}')
print(f'Date Range: {row[1]} to {row[2]}')

conn.close()
