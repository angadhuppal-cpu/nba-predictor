"""
Seed Sample Data for NBA Prediction System
Generates realistic historical data for testing predictions
"""

import sqlite3
import random
from datetime import datetime, timedelta
import numpy as np

def seed_database(db_path='../database/nba_data.db'):
    """Seed database with sample historical data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Seeding database with sample data...")

    # Sample players with realistic stats
    players = [
        {
            'id': '2544', 'name': 'LeBron James', 'team': 'LAL', 'position': 'SF',
            'avg_points': 25.0, 'avg_rebounds': 7.5, 'avg_assists': 7.8,
            'std_points': 6.0, 'std_rebounds': 2.5, 'std_assists': 2.0
        },
        {
            'id': '1627750', 'name': 'Jayson Tatum', 'team': 'BOS', 'position': 'SF',
            'avg_points': 27.0, 'avg_rebounds': 8.3, 'avg_assists': 4.9,
            'std_points': 7.0, 'std_rebounds': 2.0, 'std_assists': 1.5
        },
        {
            'id': '203999', 'name': 'Nikola Jokic', 'team': 'DEN', 'position': 'C',
            'avg_points': 24.5, 'avg_rebounds': 11.8, 'avg_assists': 9.8,
            'std_points': 5.5, 'std_rebounds': 3.0, 'std_assists': 2.5
        },
        {
            'id': '1626164', 'name': 'Devin Booker', 'team': 'PHX', 'position': 'SG',
            'avg_points': 27.1, 'avg_rebounds': 4.5, 'avg_assists': 6.7,
            'std_points': 8.0, 'std_rebounds': 1.5, 'std_assists': 1.8
        },
        {
            'id': '203507', 'name': 'Giannis Antetokounmpo', 'team': 'MIL', 'position': 'PF',
            'avg_points': 30.4, 'avg_rebounds': 11.6, 'avg_assists': 5.7,
            'std_points': 7.5, 'std_rebounds': 2.8, 'std_assists': 1.5
        },
        {
            'id': '1629029', 'name': 'Luka Doncic', 'team': 'DAL', 'position': 'PG',
            'avg_points': 28.4, 'avg_rebounds': 8.8, 'avg_assists': 8.2,
            'std_points': 7.8, 'std_rebounds': 2.5, 'std_assists': 2.2
        },
        {
            'id': '1630162', 'name': 'Anthony Edwards', 'team': 'MIN', 'position': 'SG',
            'avg_points': 25.9, 'avg_rebounds': 5.4, 'avg_assists': 5.1,
            'std_points': 6.5, 'std_rebounds': 1.8, 'std_assists': 1.7
        },
        {
            'id': '1630163', 'name': 'Tyrese Haliburton', 'team': 'IND', 'position': 'PG',
            'avg_points': 20.1, 'avg_rebounds': 3.9, 'avg_assists': 10.9,
            'std_points': 5.0, 'std_rebounds': 1.5, 'std_assists': 2.5
        },
        {
            'id': '201142', 'name': 'Kevin Durant', 'team': 'PHX', 'position': 'SF',
            'avg_points': 27.1, 'avg_rebounds': 6.7, 'avg_assists': 5.0,
            'std_points': 6.8, 'std_rebounds': 2.0, 'std_assists': 1.5
        },
        {
            'id': '201935', 'name': 'James Harden', 'team': 'LAC', 'position': 'PG',
            'avg_points': 21.2, 'avg_rebounds': 6.2, 'avg_assists': 10.8,
            'std_points': 5.5, 'std_rebounds': 1.8, 'std_assists': 2.0
        }
    ]

    # NBA teams
    teams = ['LAL', 'BOS', 'MIL', 'PHX', 'DEN', 'GSW', 'MIA', 'PHI',
             'BKN', 'LAC', 'DAL', 'MEM', 'NOP', 'SAC', 'POR', 'NYK',
             'MIN', 'IND', 'ATL', 'CHI', 'CLE', 'DET', 'HOU', 'OKC',
             'ORL', 'SAS', 'TOR', 'UTA', 'WAS', 'CHA']

    # Generate historical game data (last 30 games for each player)
    start_date = datetime(2024, 10, 1)
    games_per_player = 30

    print("Generating player game statistics...")
    for player in players:
        for game_num in range(games_per_player):
            game_date = start_date + timedelta(days=game_num * 2)  # Games every 2 days
            opponent = random.choice([t for t in teams if t != player['team']])
            is_home = random.choice([True, False])

            # Generate stats with some randomness around player averages
            points = int(np.random.normal(player['avg_points'], player['std_points']))
            points = max(0, min(points, 50))  # Cap between 0-50

            rebounds = int(np.random.normal(player['avg_rebounds'], player['std_rebounds']))
            rebounds = max(0, min(rebounds, 20))

            assists = int(np.random.normal(player['avg_assists'], player['std_assists']))
            assists = max(0, min(assists, 15))

            # Other stats
            minutes = int(np.random.normal(33, 5))
            minutes = max(15, min(minutes, 42))

            steals = max(0, int(np.random.poisson(1.2)))
            blocks = max(0, int(np.random.poisson(0.7)))
            turnovers = max(0, int(np.random.poisson(2.3)))

            # Shooting stats
            fgm = int(points * 0.4)  # Approximate FG made
            fga = int(fgm * 2.2)  # Approximate FG attempted
            three_pm = int(points * 0.15)
            three_pa = int(three_pm * 2.5)
            ftm = int(points * 0.25)
            fta = int(ftm * 1.2)

            plus_minus = random.randint(-15, 20)
            fantasy_points = (points + rebounds * 1.2 + assists * 1.5 +
                            steals * 3.0 + blocks * 3.0 - turnovers)

            # Insert game data
            cursor.execute("""
                INSERT INTO player_stats
                (player_id, player_name, team, date, opponent, is_home, minutes,
                 points, rebounds, assists, steals, blocks, turnovers,
                 field_goals_made, field_goals_attempted,
                 three_pointers_made, three_pointers_attempted,
                 free_throws_made, free_throws_attempted,
                 plus_minus, fantasy_points)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player['id'], player['name'], player['team'],
                game_date.strftime('%Y-%m-%d'), opponent, is_home, minutes,
                points, rebounds, assists, steals, blocks, turnovers,
                fgm, fga, three_pm, three_pa, ftm, fta, plus_minus, fantasy_points
            ))

    print(f"[OK] Generated {len(players) * games_per_player} game records")

    # Generate team defensive statistics
    print("Generating team statistics...")
    for team in teams:
        def_rating = np.random.normal(110, 5)  # League average around 110
        off_rating = np.random.normal(112, 6)
        pace = np.random.normal(100, 3)

        cursor.execute("""
            INSERT INTO team_stats
            (team_id, team_name, season, date, wins, losses,
             offensive_rating, defensive_rating, net_rating, pace)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            team, team, '2024-25', datetime.now().strftime('%Y-%m-%d'),
            random.randint(5, 15), random.randint(3, 12),
            off_rating, def_rating, off_rating - def_rating, pace
        ))

    print(f"[OK] Generated statistics for {len(teams)} teams")

    # Generate some sample injuries
    print("Generating injury reports...")
    injury_types = ['Ankle', 'Knee', 'Back', 'Hamstring', 'Shoulder']
    statuses = ['Questionable', 'Doubtful', 'Out']

    for _ in range(10):
        player = random.choice(players)
        injury = random.choice(injury_types)
        status = random.choice(statuses)

        cursor.execute("""
            INSERT OR IGNORE INTO injury_report
            (player_id, player_name, team, injury_type, status, report_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            player['id'], player['name'], player['team'],
            injury, status, datetime.now().strftime('%Y-%m-%d')
        ))

    print("[OK] Generated sample injury reports")

    # Generate game schedule for next 7 days
    print("Generating upcoming schedule...")
    for day in range(7):
        game_date = datetime.now() + timedelta(days=day)
        num_games = random.randint(3, 8)

        for _ in range(num_games):
            home_team = random.choice(teams)
            away_team = random.choice([t for t in teams if t != home_team])
            game_id = f"002{day:02d}{_:02d}"

            cursor.execute("""
                INSERT OR IGNORE INTO game_schedule
                (game_id, season, date, time, home_team, away_team, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id, '2024-25', game_date.strftime('%Y-%m-%d'),
                '19:30', home_team, away_team, 'Scheduled'
            ))

    print("[OK] Generated 7-day schedule")

    # Commit all changes
    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("[OK] Database seeding completed successfully!")
    print("=" * 60)
    print(f"\nData summary:")
    print(f"  - Players: {len(players)}")
    print(f"  - Game records: {len(players) * games_per_player}")
    print(f"  - Teams: {len(teams)}")
    print(f"  - Injury reports: 10")
    print(f"  - Upcoming games: ~{7 * 5}")
    print("\nYou can now make predictions with historical data!")

if __name__ == "__main__":
    import sys
    import os

    # Get database path
    db_path = sys.argv[1] if len(sys.argv) > 1 else '../database/nba_data.db'

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Please run init_db.py first to create the database")
        sys.exit(1)

    seed_database(db_path)
