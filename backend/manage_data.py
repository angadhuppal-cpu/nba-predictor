#!/usr/bin/env python3
"""
NBA Data Management CLI
Easy command-line interface for managing NBA data pipeline
"""

import sys
import argparse
from nba_data_pipeline import NBADataPipeline
from data_scheduler import DataScheduler
import sqlite3
from datetime import datetime

def show_status(db_path='../database/nba_data.db'):
    """Show current database status"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\n" + "="*60)
        print("NBA DATABASE STATUS")
        print("="*60)

        # Player stats
        cursor.execute("SELECT COUNT(DISTINCT player_name) FROM player_stats")
        unique_players = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM player_stats")
        total_games = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(date), MIN(date) FROM player_stats")
        date_range = cursor.fetchone()

        print(f"\n📊 Player Statistics:")
        print(f"  • Unique players: {unique_players}")
        print(f"  • Total game records: {total_games}")
        if date_range[0]:
            print(f"  • Date range: {date_range[1]} to {date_range[0]}")

        # Season stats
        cursor.execute("SELECT COUNT(*) FROM player_season_stats")
        season_players = cursor.fetchone()[0]
        print(f"\n📈 Season Statistics:")
        print(f"  • Players with season stats: {season_players}")

        # Teams
        cursor.execute("SELECT COUNT(DISTINCT team_name) FROM team_stats")
        teams = cursor.fetchone()[0]
        print(f"\n🏀 Teams:")
        print(f"  • NBA teams: {teams}")

        # Injuries
        cursor.execute("SELECT COUNT(*) FROM injury_report")
        injuries = cursor.fetchone()[0]
        print(f"\n🏥 Injury Reports:")
        print(f"  • Injury records: {injuries}")

        # Schedule
        cursor.execute("SELECT COUNT(*) FROM game_schedule")
        games = cursor.fetchone()[0]
        print(f"\n📅 Schedule:")
        print(f"  • Scheduled games: {games}")

        print("\n" + "="*60 + "\n")

        conn.close()
    except Exception as e:
        print(f"Error checking status: {e}")

def fetch_all_data():
    """Fetch all NBA data"""
    print("\n🚀 Starting full data fetch...")
    print("This may take several minutes...\n")

    pipeline = NBADataPipeline()
    pipeline.save_to_database()

    print("\n✅ Data fetch complete!")
    show_status()

def fetch_rosters_only():
    """Fetch only team rosters"""
    print("\n🚀 Fetching team rosters...")

    pipeline = NBADataPipeline()
    pipeline.connect_db()

    rosters = pipeline.fetch_team_rosters()
    pipeline._save_rosters_to_db(rosters)

    pipeline.close_db()

    print(f"\n✅ Fetched rosters for {len(rosters)} teams")

def fetch_stats_only():
    """Fetch only player statistics"""
    print("\n🚀 Fetching player statistics...")

    pipeline = NBADataPipeline()
    pipeline.connect_db()

    stats = pipeline.fetch_player_season_stats()
    pipeline._save_season_stats_to_db(stats)

    pipeline.close_db()

    print(f"\n✅ Fetched stats for {len(stats)} players")

def search_player(player_name):
    """Search for a player in the database"""
    try:
        conn = sqlite3.connect('../database/nba_data.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT player_name, team, games_played, points_avg, rebounds_avg, assists_avg
            FROM player_season_stats
            WHERE player_name LIKE ?
        """, (f'%{player_name}%',))

        results = cursor.fetchall()

        if results:
            print(f"\n🔍 Found {len(results)} player(s):\n")
            for player in results:
                print(f"  • {player[0]} ({player[1]})")
                print(f"    GP: {player[2]} | PPG: {player[3]:.1f} | RPG: {player[4]:.1f} | APG: {player[5]:.1f}")
                print()
        else:
            print(f"\n❌ No players found matching '{player_name}'")

        conn.close()
    except Exception as e:
        print(f"Error searching: {e}")

def list_teams():
    """List all NBA teams"""
    try:
        conn = sqlite3.connect('../database/nba_data.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT team_name, offensive_rating, defensive_rating, pace
            FROM team_stats
            ORDER BY team_name
        """)

        teams = cursor.fetchall()

        if teams:
            print(f"\n🏀 NBA Teams ({len(teams)}):\n")
            for team in teams:
                print(f"  • {team[0]}")
                if team[1]:
                    print(f"    Off Rating: {team[1]:.1f} | Def Rating: {team[2]:.1f} | Pace: {team[3]:.1f}")
                print()
        else:
            print("\n❌ No teams found in database")

        conn.close()
    except Exception as e:
        print(f"Error listing teams: {e}")

def start_scheduler():
    """Start the automated data scheduler"""
    print("\n⏰ Starting automated data scheduler...")
    print("The scheduler will run in the background and update data:")
    print("  • Full update: Daily at 3:00 AM")
    print("  • Quick update: Every 6 hours")
    print("\nPress Ctrl+C to stop.\n")

    scheduler = DataScheduler()
    scheduler.start()

    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        print("\n\n⏹️  Stopping scheduler...")
        scheduler.stop()
        print("✅ Scheduler stopped")

def main():
    parser = argparse.ArgumentParser(
        description='NBA Data Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status              Show database status
  %(prog)s fetch               Fetch all NBA data
  %(prog)s fetch-rosters       Fetch team rosters only
  %(prog)s fetch-stats         Fetch player stats only
  %(prog)s search "LeBron"     Search for a player
  %(prog)s teams               List all teams
  %(prog)s schedule            Start automated scheduler
        """
    )

    parser.add_argument('command', choices=[
        'status', 'fetch', 'fetch-rosters', 'fetch-stats',
        'search', 'teams', 'schedule'
    ], help='Command to execute')

    parser.add_argument('args', nargs='*', help='Additional arguments')

    args = parser.parse_args()

    if args.command == 'status':
        show_status()

    elif args.command == 'fetch':
        fetch_all_data()

    elif args.command == 'fetch-rosters':
        fetch_rosters_only()

    elif args.command == 'fetch-stats':
        fetch_stats_only()

    elif args.command == 'search':
        if not args.args:
            print("Error: Please provide a player name to search")
            sys.exit(1)
        search_player(' '.join(args.args))

    elif args.command == 'teams':
        list_teams()

    elif args.command == 'schedule':
        start_scheduler()

if __name__ == '__main__':
    main()
