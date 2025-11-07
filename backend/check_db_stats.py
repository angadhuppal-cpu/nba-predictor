import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM player_season_stats')
print(f'Player-season records: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM player_stats')
print(f'Game records: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(DISTINCT season) FROM player_season_stats')
print(f'Total seasons: {cursor.fetchone()[0]}')

cursor.execute('SELECT DISTINCT season FROM player_season_stats ORDER BY season')
print('\nSeasons in database:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')

cursor.execute('SELECT COUNT(DISTINCT player_name) FROM player_stats')
print(f'\nPlayers with game history: {cursor.fetchone()[0]}')

conn.close()
