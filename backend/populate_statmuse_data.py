#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-populate StatMuse Data for Top Players
Run this script periodically to cache granular statistics
This avoids slow scraping during live predictions
"""

import sys
import io
import sqlite3
from statmuse_scraper import StatMuseScraper
import time

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_top_players(db_path='../database/nba_data.db', limit=50):
    """Get top players by points average"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT player_name, team, points_avg
        FROM player_season_stats
        WHERE season = '2025-26' AND games_played >= 5
        ORDER BY points_avg DESC
        LIMIT ?
    """, (limit,))

    players = cursor.fetchall()
    conn.close()

    return [(name, team) for name, team, _ in players]

def get_all_teams():
    """Get all NBA teams"""
    return [
        'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
        'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
        'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
        'LA Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
        'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
        'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
        'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
        'Utah Jazz', 'Washington Wizards'
    ]

def populate_key_matchups(top_n_players=30):
    """
    Populate StatMuse data for top players vs division rivals and key matchups
    This focuses on likely matchups rather than all combinations
    """
    print("="*70)
    print("POPULATING STATMUSE DATA FOR KEY MATCHUPS")
    print("="*70)

    scraper = StatMuseScraper()
    top_players = get_top_players(limit=top_n_players)

    # Define key matchup teams (division rivals, popular matchups)
    key_matchups = {
        'Los Angeles Lakers': ['Golden State Warriors', 'LA Clippers', 'Phoenix Suns', 'Boston Celtics'],
        'Golden State Warriors': ['Los Angeles Lakers', 'LA Clippers', 'Phoenix Suns', 'Sacramento Kings'],
        'Boston Celtics': ['Miami Heat', 'Philadelphia 76ers', 'Milwaukee Bucks', 'Los Angeles Lakers'],
        'Milwaukee Bucks': ['Boston Celtics', 'Philadelphia 76ers', 'Miami Heat', 'Chicago Bulls'],
        'Phoenix Suns': ['Los Angeles Lakers', 'Golden State Warriors', 'Dallas Mavericks', 'Denver Nuggets'],
        'Dallas Mavericks': ['Phoenix Suns', 'Denver Nuggets', 'Houston Rockets', 'San Antonio Spurs'],
        'Miami Heat': ['Boston Celtics', 'Philadelphia 76ers', 'Milwaukee Bucks', 'Atlanta Hawks'],
        'Denver Nuggets': ['Phoenix Suns', 'Minnesota Timberwolves', 'Portland Trail Blazers', 'Utah Jazz'],
    }

    total_fetched = 0

    for idx, (player_name, player_team) in enumerate(top_players, 1):
        print(f"\n[{idx}/{top_n_players}] {player_name} ({player_team})")
        print("-" * 70)

        # Get key matchups for this player's team
        opponents = key_matchups.get(player_team, [
            'Los Angeles Lakers', 'Boston Celtics', 'Golden State Warriors'  # Default to popular teams
        ])

        for opponent in opponents[:3]:  # Limit to top 3 opponents per player
            try:
                # Fetch comprehensive stats
                stats = scraper.fetch_comprehensive_player_stats(
                    player_name=player_name,
                    opponent_team=opponent
                )

                if stats:
                    total_fetched += 1

                # Rate limiting: wait between requests
                time.sleep(scraper.rate_limit_delay)

            except Exception as e:
                print(f"  ✗ Error for {player_name} vs {opponent}: {e}")
                continue

    print("\n" + "="*70)
    print(f"✅ COMPLETE! Populated {total_fetched} matchup datasets")
    print("="*70)

def populate_all_players_recent_form(top_n_players=50):
    """
    Populate recent form for top players (no opponent needed)
    This is quick and useful for all predictions
    """
    print("\n" + "="*70)
    print("POPULATING RECENT FORM FOR TOP PLAYERS")
    print("="*70)

    scraper = StatMuseScraper()
    top_players = get_top_players(limit=top_n_players)

    for idx, (player_name, player_team) in enumerate(top_players, 1):
        print(f"\n[{idx}/{top_n_players}] {player_name}")

        try:
            # Fetch recent form (last 5 games)
            recent_form = scraper.fetch_recent_form(player_name, last_n_games=5)
            if recent_form:
                scraper.save_to_database(recent_form, 'recent_form_5')

            # Fetch home/away splits
            splits = scraper.fetch_home_away_splits(player_name)
            if splits:
                scraper.save_to_database(splits, 'home_away_splits')

            # Fetch clutch stats
            clutch = scraper.fetch_clutch_stats(player_name)
            if clutch:
                scraper.save_to_database(clutch, 'clutch_stats')

            time.sleep(scraper.rate_limit_delay)

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\n" + "="*70)
    print("✅ COMPLETE! Recent form data populated")
    print("="*70)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Populate StatMuse data')
    parser.add_argument('--mode', choices=['matchups', 'form', 'full'], default='form',
                        help='Mode: matchups (player vs opponents), form (recent stats), full (both)')
    parser.add_argument('--players', type=int, default=30,
                        help='Number of top players to process')

    args = parser.parse_args()

    if args.mode in ['form', 'full']:
        populate_all_players_recent_form(top_n_players=args.players)

    if args.mode in ['matchups', 'full']:
        populate_key_matchups(top_n_players=args.players)

    print("\n🎉 All done! StatMuse data is now cached in the database.")
    print("💡 Run predictions to see the enhanced granular statistics in action!")
