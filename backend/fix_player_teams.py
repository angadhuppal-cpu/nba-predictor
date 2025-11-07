"""
Fix incorrect player team assignments
"""
import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

# Check and fix Luka Doncic
cursor.execute("""
    SELECT season, team, points_avg
    FROM player_season_stats
    WHERE player_name LIKE 'Luka%'
    ORDER BY season
""")

print("Luka Doncic current assignments:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]:.1f} PPG)")

# Fix Luka's team to DAL
cursor.execute("""
    UPDATE player_season_stats
    SET team = 'DAL'
    WHERE player_name LIKE 'Luka%' AND team != 'DAL'
""")
print(f"\nFixed {cursor.rowcount} season records for Luka")

cursor.execute("""
    UPDATE player_stats
    SET team = 'DAL'
    WHERE player_name LIKE 'Luka%' AND team != 'DAL'
""")
print(f"Fixed {cursor.rowcount} game records for Luka")

# Check for other potential issues - players who shouldn't be on certain teams
known_fixes = [
    ('Anthony Davis', 'LAL'),  # Not DAL
    ('De\'Aaron Fox', 'SAC'),  # Not SAS
    ('Zach LaVine', 'CHI'),    # Not SAC
    ('Desmond Bane', 'MEM'),   # Not ORL
    ('Jimmy Butler', 'MIA'),   # Not GSW
    ('De\'Andre Hunter', 'ATL'), # Not CLE
]

print("\nChecking other potential team errors...")
for player_name, correct_team in known_fixes:
    cursor.execute("""
        SELECT DISTINCT team FROM player_season_stats
        WHERE player_name = ? AND season = '2024-25'
    """, (player_name,))

    result = cursor.fetchone()
    if result and result[0] != correct_team:
        print(f"  {player_name}: {result[0]} -> {correct_team}")

        cursor.execute("""
            UPDATE player_season_stats
            SET team = ?
            WHERE player_name = ? AND season = '2024-25'
        """, (correct_team, player_name))

        cursor.execute("""
            UPDATE player_stats
            SET team = ?
            WHERE player_name = ? AND date >= '2024-10-01'
        """, (correct_team, player_name))

conn.commit()
print("\n[OK] Team assignments corrected!")

# Verify fixes
print("\nVerification - Top 10 scorers 2024-25:")
cursor.execute("""
    SELECT player_name, team, points_avg
    FROM player_season_stats
    WHERE season = '2024-25'
    ORDER BY points_avg DESC
    LIMIT 10
""")

for name, team, ppg in cursor.fetchall():
    print(f"  {name:30s} {team:5s} {ppg:5.1f} PPG")

conn.close()
