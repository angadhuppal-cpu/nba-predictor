#!/usr/bin/env python3
"""
Clean up team names to use full names only (no abbreviations)
"""
import sqlite3

# Team abbreviation to full name mapping
TEAM_MAPPING = {
    'ATL': 'Atlanta Hawks',
    'BOS': 'Boston Celtics',
    'BKN': 'Brooklyn Nets',
    'CHA': 'Charlotte Hornets',
    'CHI': 'Chicago Bulls',
    'CLE': 'Cleveland Cavaliers',
    'DAL': 'Dallas Mavericks',
    'DEN': 'Denver Nuggets',
    'DET': 'Detroit Pistons',
    'GSW': 'Golden State Warriors',
    'HOU': 'Houston Rockets',
    'IND': 'Indiana Pacers',
    'LAC': 'LA Clippers',
    'LAL': 'Los Angeles Lakers',
    'MEM': 'Memphis Grizzlies',
    'MIA': 'Miami Heat',
    'MIL': 'Milwaukee Bucks',
    'MIN': 'Minnesota Timberwolves',
    'NOP': 'New Orleans Pelicans',
    'NYK': 'New York Knicks',
    'OKC': 'Oklahoma City Thunder',
    'ORL': 'Orlando Magic',
    'PHI': 'Philadelphia 76ers',
    'PHX': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers',
    'SAC': 'Sacramento Kings',
    'SAS': 'San Antonio Spurs',
    'TOR': 'Toronto Raptors',
    'UTA': 'Utah Jazz',
    'WAS': 'Washington Wizards'
}

def cleanup_team_names():
    conn = sqlite3.connect('../database/nba_data.db')
    cursor = conn.cursor()

    print("Starting team name cleanup...")
    print("="*60)

    # 1. Update player_stats table
    print("\n1. Cleaning player_stats...")
    for abbrev, full_name in TEAM_MAPPING.items():
        cursor.execute("""
            UPDATE player_stats
            SET team = ?, opponent = ?
            WHERE team = ? OR opponent = ?
        """, (full_name, full_name, abbrev, abbrev))

    cursor.execute("SELECT COUNT(*) FROM player_stats")
    print(f"   Updated player_stats: {cursor.fetchone()[0]} records")

    # 2. Update player_season_stats table
    print("\n2. Cleaning player_season_stats...")
    for abbrev, full_name in TEAM_MAPPING.items():
        cursor.execute("""
            UPDATE player_season_stats
            SET team = ?
            WHERE team = ?
        """, (full_name, abbrev))

    cursor.execute("SELECT COUNT(*) FROM player_season_stats")
    print(f"   Updated player_season_stats: {cursor.fetchone()[0]} records")

    # 3. Update team_stats table
    print("\n3. Cleaning team_stats...")
    for abbrev, full_name in TEAM_MAPPING.items():
        cursor.execute("""
            UPDATE team_stats
            SET team_name = ?
            WHERE team_name = ?
        """, (full_name, abbrev))

    # Remove duplicate team entries (keep only full names)
    cursor.execute("""
        DELETE FROM team_stats
        WHERE team_name IN (
            SELECT team_name
            FROM team_stats
            GROUP BY team_id
            HAVING COUNT(*) > 1
        )
        AND LENGTH(team_name) <= 3
    """)

    cursor.execute("SELECT COUNT(DISTINCT team_name) FROM team_stats")
    print(f"   Unique teams in team_stats: {cursor.fetchone()[0]}")

    # 4. Update injury_report table
    print("\n4. Cleaning injury_report...")
    for abbrev, full_name in TEAM_MAPPING.items():
        cursor.execute("""
            UPDATE injury_report
            SET team = ?
            WHERE team = ?
        """, (full_name, abbrev))

    cursor.execute("SELECT COUNT(*) FROM injury_report")
    print(f"   Updated injury_report: {cursor.fetchone()[0]} records")

    # 5. Update game_schedule table
    print("\n5. Cleaning game_schedule...")
    for abbrev, full_name in TEAM_MAPPING.items():
        cursor.execute("""
            UPDATE game_schedule
            SET home_team = ?, away_team = ?
            WHERE home_team = ? OR away_team = ?
        """, (full_name, full_name, abbrev, abbrev))

    cursor.execute("SELECT COUNT(*) FROM game_schedule")
    print(f"   Updated game_schedule: {cursor.fetchone()[0]} records")

    conn.commit()

    # Verify cleanup
    print("\n" + "="*60)
    print("Verification:")
    print("="*60)

    cursor.execute("SELECT DISTINCT team_name FROM team_stats ORDER BY team_name")
    teams = cursor.fetchall()
    print(f"\nTeams in team_stats ({len(teams)} total):")
    for team in teams:
        print(f"  ✓ {team[0]}")

    conn.close()

    print("\n" + "="*60)
    print("✅ Cleanup complete!")
    print("="*60)

if __name__ == '__main__':
    cleanup_team_names()
