"""
Populate player_season_stats from player_stats data
"""
import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

# Get distinct players from player_stats
cursor.execute("""
    SELECT DISTINCT player_id, player_name, team
    FROM player_stats
""")
players = cursor.fetchall()

print(f"Found {len(players)} players in player_stats")

# For each player, calculate season averages
for player_id, player_name, team in players:
    cursor.execute("""
        SELECT
            COUNT(*) as games_played,
            AVG(minutes) as minutes_avg,
            AVG(points) as points_avg,
            AVG(rebounds) as rebounds_avg,
            AVG(assists) as assists_avg,
            AVG(steals) as steals_avg,
            AVG(blocks) as blocks_avg,
            AVG(turnovers) as turnovers_avg,
            AVG(CAST(field_goals_made AS FLOAT) / NULLIF(field_goals_attempted, 0)) as field_goal_pct,
            AVG(CAST(three_pointers_made AS FLOAT) / NULLIF(three_pointers_attempted, 0)) as three_point_pct,
            AVG(CAST(free_throws_made AS FLOAT) / NULLIF(free_throws_attempted, 0)) as free_throw_pct
        FROM player_stats
        WHERE player_id = ?
    """, (player_id,))

    stats = cursor.fetchone()

    # Insert into player_season_stats
    cursor.execute("""
        INSERT OR REPLACE INTO player_season_stats
        (player_id, player_name, team, season, games_played, minutes_avg,
         points_avg, rebounds_avg, assists_avg, steals_avg, blocks_avg,
         turnovers_avg, field_goal_pct, three_point_pct, free_throw_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        player_id, player_name, team, '2024-25',
        stats[0], stats[1], stats[2], stats[3], stats[4],
        stats[5], stats[6], stats[7], stats[8], stats[9], stats[10]
    ))

    print(f"  {player_name}: {stats[2]:.1f} PPG, {stats[3]:.1f} RPG, {stats[4]:.1f} APG")

conn.commit()
print(f"\n[OK] Populated season stats for {len(players)} players")
conn.close()
