#!/usr/bin/env python3
"""
Populate Usage Rates for All NBA Players
Fetches real usage rates from NBA Stats API and caches them in database
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
from nba_data_fetcher import NBADataFetcher
from datetime import datetime
import time

def create_usage_rates_table():
    """Create table to store usage rates"""
    conn = sqlite3.connect('../database/nba_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_usage_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT UNIQUE NOT NULL,
            usage_rate REAL NOT NULL,
            true_shooting_pct REAL,
            assist_pct REAL,
            season TEXT NOT NULL,
            source TEXT NOT NULL,
            fetched_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index for fast lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_player_usage
        ON player_usage_rates(player_name, season)
    ''')

    conn.commit()
    conn.close()
    print("[OK] Usage rates table created")

def get_all_active_players():
    """Get all active players from database"""
    conn = sqlite3.connect('../database/nba_data.db')
    cursor = conn.cursor()

    # Get players from current season with at least 5 games played
    cursor.execute("""
        SELECT DISTINCT player_name, team, games_played
        FROM player_season_stats
        WHERE season = '2025-26' AND games_played >= 5
        ORDER BY games_played DESC
    """)

    players = cursor.fetchall()
    conn.close()

    return [(row[0], row[1]) for row in players]

def populate_all_usage_rates():
    """Fetch and store usage rates for all active players"""
    print("="*70)
    print("FETCHING USAGE RATES FOR ALL NBA PLAYERS")
    print("="*70)

    # Create table
    create_usage_rates_table()

    # Get all players
    players = get_all_active_players()
    print(f"\nFound {len(players)} active players in 2025-26 season")
    print("-"*70)

    # Initialize data fetcher
    fetcher = NBADataFetcher()

    # Fetch advanced stats for all players at once (more efficient)
    print("\nFetching advanced stats from NBA API...")
    try:
        df = fetcher.fetch_player_advanced_stats(season='2025-26')
        print(f"[OK] Fetched advanced stats for {len(df)} players")
    except Exception as e:
        print(f"[X] Error fetching advanced stats: {e}")
        return

    # Connect to database
    conn = sqlite3.connect('../database/nba_data.db')
    cursor = conn.cursor()

    successful_count = 0
    failed_count = 0

    # Process each player
    for idx, (player_name, team) in enumerate(players, 1):
        try:
            # Find player in advanced stats DataFrame
            player_data = df[df['PLAYER_NAME'] == player_name]

            if player_data.empty:
                print(f"[{idx}/{len(players)}] {player_name:<30} - Not found in API data")
                failed_count += 1
                continue

            # Extract usage rate and other advanced stats
            usage_pct = player_data.iloc[0].get('USG_PCT', None)
            ts_pct = player_data.iloc[0].get('TS_PCT', None)
            ast_pct = player_data.iloc[0].get('AST_PCT', None)

            if usage_pct is None:
                print(f"[{idx}/{len(players)}] {player_name:<30} - No usage rate data")
                failed_count += 1
                continue

            # Convert to percentage (0.387 -> 38.7%)
            usage_rate = float(usage_pct) * 100.0
            true_shooting = float(ts_pct) * 100.0 if ts_pct else None
            assist_percentage = float(ast_pct) if ast_pct else None

            # Insert or update in database
            cursor.execute('''
                INSERT OR REPLACE INTO player_usage_rates
                (player_name, usage_rate, true_shooting_pct, assist_pct, season, source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                player_name,
                usage_rate,
                true_shooting,
                assist_percentage,
                '2025-26',
                'NBA Stats API',
                datetime.now()
            ))

            print(f"[{idx}/{len(players)}] {player_name:<30} USG: {usage_rate:>5.1f}%  TS: {true_shooting:>5.1f}% ({team})")
            successful_count += 1

            # Commit every 50 players
            if idx % 50 == 0:
                conn.commit()
                print(f"\n[OK] Saved {idx} players to database\n")

        except Exception as e:
            print(f"[{idx}/{len(players)}] {player_name:<30} - Error: {e}")
            failed_count += 1

    # Final commit
    conn.commit()
    conn.close()

    print("\n" + "="*70)
    print(f"[OK] COMPLETE! Usage rates populated")
    print(f"    Successful: {successful_count}")
    print(f"    Failed:     {failed_count}")
    print(f"    Total:      {len(players)}")
    print("="*70)

def verify_usage_rates():
    """Verify that usage rates are stored correctly"""
    conn = sqlite3.connect('../database/nba_data.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT player_name, usage_rate, true_shooting_pct, source
        FROM player_usage_rates
        WHERE season = '2025-26'
        ORDER BY usage_rate DESC
        LIMIT 10
    """)

    top_players = cursor.fetchall()
    conn.close()

    print("\n" + "="*70)
    print("TOP 10 HIGHEST USAGE RATES:")
    print("-"*70)
    print(f"{'Player':<30} {'Usage Rate':<15} {'TS%':<10} {'Source'}")
    print("-"*70)

    for player, usage, ts, source in top_players:
        ts_str = f"{ts:.1f}%" if ts else "N/A"
        print(f"{player:<30} {usage:>6.1f}%        {ts_str:<10} {source}")

    print("="*70)

if __name__ == '__main__':
    populate_all_usage_rates()
    verify_usage_rates()
