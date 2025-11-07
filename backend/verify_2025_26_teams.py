"""
Verify 2025-26 season player teams
"""
import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

print('=' * 70)
print('TOP 20 SCORERS - 2025-26 SEASON')
print('=' * 70)

cursor.execute("""
    SELECT player_name, team, points_avg, games_played
    FROM player_season_stats
    WHERE season = '2025-26' AND games_played >= 5
    ORDER BY points_avg DESC
    LIMIT 20
""")

for i, (name, team, ppg, gp) in enumerate(cursor.fetchall(), 1):
    print(f'{i:2d}. {name:30s} {team:5s} {ppg:5.1f} PPG ({gp:2d} GP)')

print('\n' + '=' * 70)
print('NOTABLE PLAYERS - 2025-26 TEAM ASSIGNMENTS')
print('=' * 70)

notable_players = [
    'LeBron James', 'Stephen Curry', 'Kevin Durant', 'Giannis Antetokounmpo',
    'Luka Doncic', 'Joel Embiid', 'Anthony Davis', 'Damian Lillard',
    'Chris Paul', 'James Harden', 'Tyrese Maxey', 'Shai Gilgeous-Alexander'
]

for player in notable_players:
    cursor.execute("""
        SELECT player_name, team, points_avg, games_played
        FROM player_season_stats
        WHERE player_name LIKE ? AND season = '2025-26'
    """, (f'%{player}%',))

    result = cursor.fetchone()
    if result:
        name, team, ppg, gp = result
        print(f'{name:30s} {team:5s} {ppg:5.1f} PPG ({gp:2d} GP)')
    else:
        print(f'{player:30s} NOT FOUND')

conn.close()
print('=' * 70)
