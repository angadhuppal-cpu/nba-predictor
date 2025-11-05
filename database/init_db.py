"""
Database Initialization Script
Creates all necessary tables and indexes for the NBA Prediction System
"""

import sqlite3
import os
from datetime import datetime

def init_database(db_path='nba_data.db'):
    """Initialize the database with all required tables"""

    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Initializing database at: {db_path}")

    # Drop existing tables (optional - comment out if you want to preserve data)
    # cursor.execute('DROP TABLE IF EXISTS player_stats')
    # cursor.execute('DROP TABLE IF EXISTS team_stats')
    # cursor.execute('DROP TABLE IF EXISTS injury_report')
    # cursor.execute('DROP TABLE IF EXISTS game_schedule')

    # Player stats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            player_name TEXT NOT NULL,
            team TEXT,
            date DATE NOT NULL,
            opponent TEXT,
            is_home BOOLEAN,
            minutes REAL,
            points INTEGER,
            rebounds INTEGER,
            assists INTEGER,
            steals INTEGER,
            blocks INTEGER,
            turnovers INTEGER,
            field_goals_made INTEGER,
            field_goals_attempted INTEGER,
            three_pointers_made INTEGER,
            three_pointers_attempted INTEGER,
            free_throws_made INTEGER,
            free_throws_attempted INTEGER,
            plus_minus INTEGER,
            fantasy_points REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_id, date)
        )
    ''')

    # Create indexes for player_stats
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_stats_player_id
        ON player_stats(player_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_stats_date
        ON player_stats(date)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_stats_opponent
        ON player_stats(opponent)
    ''')

    # Team stats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id TEXT NOT NULL,
            team_name TEXT NOT NULL,
            season TEXT,
            date DATE,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            offensive_rating REAL,
            defensive_rating REAL,
            net_rating REAL,
            pace REAL,
            true_shooting_pct REAL,
            home_record TEXT,
            away_record TEXT,
            last_10_record TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(team_id, date)
        )
    ''')

    # Create indexes for team_stats
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_team_stats_team_id
        ON team_stats(team_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_team_stats_date
        ON team_stats(date)
    ''')

    # Injury report table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS injury_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            player_name TEXT NOT NULL,
            team TEXT,
            injury_type TEXT,
            injury_description TEXT,
            status TEXT,
            return_date DATE,
            games_missed INTEGER DEFAULT 0,
            report_date DATE NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_id, report_date)
        )
    ''')

    # Create indexes for injury_report
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_injury_report_player_id
        ON injury_report(player_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_injury_report_status
        ON injury_report(status)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_injury_report_date
        ON injury_report(report_date)
    ''')

    # Game schedule table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL UNIQUE,
            season TEXT,
            date DATE NOT NULL,
            time TEXT,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            home_team_score INTEGER,
            away_team_score INTEGER,
            status TEXT DEFAULT 'Scheduled',
            arena TEXT,
            attendance INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indexes for game_schedule
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_schedule_date
        ON game_schedule(date)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_schedule_home_team
        ON game_schedule(home_team)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_schedule_away_team
        ON game_schedule(away_team)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_game_schedule_game_id
        ON game_schedule(game_id)
    ''')

    # Player season stats table (aggregated data)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_season_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            player_name TEXT NOT NULL,
            team TEXT,
            season TEXT NOT NULL,
            games_played INTEGER,
            minutes_avg REAL,
            points_avg REAL,
            rebounds_avg REAL,
            assists_avg REAL,
            steals_avg REAL,
            blocks_avg REAL,
            turnovers_avg REAL,
            field_goal_pct REAL,
            three_point_pct REAL,
            free_throw_pct REAL,
            usage_rate REAL,
            true_shooting_pct REAL,
            player_efficiency_rating REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_id, season)
        )
    ''')

    # Predictions log table (for tracking and analysis)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            player_name TEXT NOT NULL,
            opponent TEXT,
            game_date DATE NOT NULL,
            predicted_points REAL,
            actual_points INTEGER,
            predicted_rebounds REAL,
            actual_rebounds INTEGER,
            predicted_assists REAL,
            actual_assists INTEGER,
            confidence_score REAL,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result_updated_at TIMESTAMP
        )
    ''')

    # Commit changes
    conn.commit()

    print("✓ Database tables created successfully")
    print("\nCreated tables:")
    print("  - player_stats")
    print("  - team_stats")
    print("  - injury_report")
    print("  - game_schedule")
    print("  - player_season_stats")
    print("  - predictions_log")
    print("\n✓ Database initialization complete!")

    # Close connection
    conn.close()

def verify_database(db_path='nba_data.db'):
    """Verify database structure"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print("\nDatabase verification:")
    print(f"Database path: {db_path}")
    print(f"Tables found: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")

    conn.close()

if __name__ == "__main__":
    # Initialize database
    db_path = os.path.join(os.path.dirname(__file__), 'nba_data.db')
    init_database(db_path)
    verify_database(db_path)
