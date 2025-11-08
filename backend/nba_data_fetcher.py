"""
NBA Data Fetcher - Real-time statistics and data collection
Fetches data from multiple sources for comprehensive analysis:
- NBA Stats API (Official NBA statistics)
- ESPN (Injury reports, schedules)
- Basketball Reference (Historical data)
- StatMuse (Granular matchup stats, splits, clutch performance)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from bs4 import BeautifulSoup
import sqlite3

class NBADataFetcher:
    """
    Fetches real-time NBA data from multiple sources:
    - Player statistics
    - Team statistics
    - Injury reports
    - Game schedules
    - Historical matchups
    """

    def __init__(self, db_path='nba_data.db'):
        self.base_urls = {
            'nba_stats': 'https://stats.nba.com/stats',
            'espn': 'https://www.espn.com/nba',
            'basketball_ref': 'https://www.basketball-reference.com',
            'statmuse': 'https://www.statmuse.com'
        }

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://stats.nba.com/',
            'Connection': 'keep-alive'
        }

        # Initialize database for caching
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for data storage"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Player stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT,
                player_name TEXT,
                team TEXT,
                date DATE,
                opponent TEXT,
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Team stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id TEXT,
                team_name TEXT,
                date DATE,
                wins INTEGER,
                losses INTEGER,
                offensive_rating REAL,
                defensive_rating REAL,
                pace REAL,
                home_record TEXT,
                away_record TEXT,
                last_10_record TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Injury report table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS injury_report (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT,
                player_name TEXT,
                team TEXT,
                injury_type TEXT,
                status TEXT,
                return_date DATE,
                games_missed INTEGER,
                report_date DATE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Game schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT,
                date DATE,
                home_team TEXT,
                away_team TEXT,
                home_team_score INTEGER,
                away_team_score INTEGER,
                status TEXT,
                arena TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def fetch_player_season_stats(self, season='2024-25'):
        """Fetch current season stats for all players"""
        endpoint = f"{self.base_urls['nba_stats']}/leaguedashplayerstats"

        params = {
            'MeasureType': 'Base',
            'PerMode': 'PerGame',
            'Season': season,
            'SeasonType': 'Regular Season',
            'Outcome': '',
            'Location': '',
            'Month': 0,
            'SeasonSegment': '',
            'DateFrom': '',
            'DateTo': '',
            'OpponentTeamID': 0,
            'VsConference': '',
            'VsDivision': '',
            'TeamID': 0,
            'Conference': '',
            'Division': '',
            'GameSegment': '',
            'Period': 0,
            'ShotClockRange': '',
            'LastNGames': 0
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                headers = data['resultSets'][0]['headers']
                rows = data['resultSets'][0]['rowSet']

                df = pd.DataFrame(rows, columns=headers)

                # Save to database
                df.to_sql('player_season_stats', self.conn, if_exists='replace', index=False)

                return df
            else:
                print(f"Error fetching data: {response.status_code}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()

    def fetch_player_game_log(self, player_id, season='2024-25'):
        """Fetch detailed game log for a specific player"""
        endpoint = f"{self.base_urls['nba_stats']}/playergamelog"

        params = {
            'PlayerID': player_id,
            'Season': season,
            'SeasonType': 'Regular Season'
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                headers = data['resultSets'][0]['headers']
                rows = data['resultSets'][0]['rowSet']

                df = pd.DataFrame(rows, columns=headers)
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            print(f"Error fetching game log: {e}")
            return pd.DataFrame()

    def fetch_player_advanced_stats(self, season='2024-25'):
        """Fetch advanced player stats including Usage Rate from NBA Stats API"""
        endpoint = f"{self.base_urls['nba_stats']}/leaguedashplayerstats"

        params = {
            'MeasureType': 'Advanced',  # Get advanced metrics
            'PerMode': 'PerGame',
            'Season': season,
            'SeasonType': 'Regular Season',
            'Outcome': '',
            'Location': '',
            'Month': 0,
            'SeasonSegment': '',
            'DateFrom': '',
            'DateTo': '',
            'OpponentTeamID': 0,
            'VsConference': '',
            'VsDivision': '',
            'TeamID': 0,
            'Conference': '',
            'Division': '',
            'GameSegment': '',
            'Period': 0,
            'ShotClockRange': '',
            'LastNGames': 0
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                headers = data['resultSets'][0]['headers']
                rows = data['resultSets'][0]['rowSet']

                df = pd.DataFrame(rows, columns=headers)

                # Extract relevant advanced stats
                # USG_PCT = Usage Percentage
                # TS_PCT = True Shooting Percentage
                # AST_PCT = Assist Percentage

                print(f"Fetched advanced stats for {len(df)} players")
                return df
            else:
                print(f"Error fetching advanced stats: {response.status_code}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()

    def get_player_usage_rate(self, player_name, season='2024-25'):
        """Get real usage rate for a specific player from NBA Stats API"""
        df = self.fetch_player_advanced_stats(season)

        if df.empty:
            return None

        # Find player in dataframe
        player_data = df[df['PLAYER_NAME'] == player_name]

        if player_data.empty:
            return None

        # Get usage percentage (USG_PCT from NBA API is a decimal like 0.387 for 38.7%)
        usage_pct = player_data.iloc[0].get('USG_PCT', None)

        return {
            'usage_rate': float(usage_pct) * 100.0 if usage_pct else None,  # Convert to percentage
            'true_shooting_pct': float(player_data.iloc[0].get('TS_PCT', 0)),  # Already decimal (0.636 = 63.6%)
            'assist_pct': float(player_data.iloc[0].get('AST_PCT', 0)) * 100.0,  # Convert to percentage
            'rebound_pct': float(player_data.iloc[0].get('REB_PCT', 0)) * 100.0,  # Convert to percentage
            'source': 'NBA Stats API'
        }

    def fetch_team_stats(self, season='2024-25'):
        """Fetch current team statistics"""
        endpoint = f"{self.base_urls['nba_stats']}/leaguedashteamstats"

        params = {
            'MeasureType': 'Advanced',
            'PerMode': 'PerGame',
            'Season': season,
            'SeasonType': 'Regular Season',
            'Month': 0,
            'LastNGames': 0
        }

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                headers = data['resultSets'][0]['headers']
                rows = data['resultSets'][0]['rowSet']

                df = pd.DataFrame(rows, columns=headers)

                # Save to database
                for _, row in df.iterrows():
                    cursor = self.conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO team_stats
                        (team_id, team_name, offensive_rating, defensive_rating, pace)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (row['TEAM_ID'], row['TEAM_NAME'],
                         row['OFF_RATING'], row['DEF_RATING'], row['PACE']))

                self.conn.commit()
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            print(f"Error fetching team stats: {e}")
            return pd.DataFrame()

    def fetch_injury_report(self):
        """Fetch current NBA injury report"""
        # This would typically scrape from ESPN or other sources
        # For demonstration, creating sample structure

        injuries = []

        # In production, would scrape actual injury reports
        # Example structure:
        sample_injuries = [
            {'player': 'Player A', 'team': 'LAL', 'injury': 'Ankle', 'status': 'Questionable'},
            {'player': 'Player B', 'team': 'BOS', 'injury': 'Knee', 'status': 'Out'},
        ]

        for injury in sample_injuries:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO injury_report
                (player_name, team, injury_type, status, report_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (injury['player'], injury['team'], injury['injury'],
                 injury['status'], datetime.now().date()))

        self.conn.commit()
        return pd.DataFrame(sample_injuries)

    def fetch_schedule(self, date=None):
        """Fetch NBA schedule for a specific date"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        # This would fetch from NBA API
        # Example structure:
        games = []

        # In production, would fetch actual schedule
        sample_games = [
            {
                'game_id': '001',
                'date': date,
                'home_team': 'Lakers',
                'away_team': 'Warriors',
                'time': '19:30'
            }
        ]

        for game in sample_games:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO game_schedule
                (game_id, date, home_team, away_team, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (game['game_id'], game['date'], game['home_team'],
                 game['away_team'], 'Scheduled'))

        self.conn.commit()
        return pd.DataFrame(sample_games)

    def get_head_to_head(self, player_id, opponent_team, limit=10):
        """Get player's recent performance against specific team"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM player_stats
            WHERE player_id = ? AND opponent = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (player_id, opponent_team, limit))

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        return pd.DataFrame(rows, columns=columns)

    def get_recent_form(self, player_id, games=5):
        """Get player's recent form over last N games"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM player_stats
            WHERE player_id = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (player_id, games))

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        df = pd.DataFrame(rows, columns=columns)

        if not df.empty:
            return {
                'avg_points': df['points'].mean(),
                'avg_rebounds': df['rebounds'].mean(),
                'avg_assists': df['assists'].mean(),
                'avg_minutes': df['minutes'].mean(),
                'trend': self.calculate_trend(df['points'].values)
            }

        return {}

    def calculate_trend(self, values):
        """Calculate performance trend (improving/declining)"""
        if len(values) < 2:
            return 'stable'

        # Simple linear regression for trend
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)

        if coefficients[0] > 0.5:
            return 'improving'
        elif coefficients[0] < -0.5:
            return 'declining'
        else:
            return 'stable'

    def get_back_to_back_games(self, team, date):
        """Check if team plays back-to-back games"""
        cursor = self.conn.cursor()

        # Check yesterday
        yesterday = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT * FROM game_schedule
            WHERE date = ? AND (home_team = ? OR away_team = ?)
        ''', (yesterday, team, team))

        yesterday_game = cursor.fetchone()

        # Check tomorrow
        tomorrow = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT * FROM game_schedule
            WHERE date = ? AND (home_team = ? OR away_team = ?)
        ''', (tomorrow, team, team))

        tomorrow_game = cursor.fetchone()

        return {
            'is_second_night': yesterday_game is not None,
            'has_game_tomorrow': tomorrow_game is not None,
            'rest_days': self.calculate_rest_days(team, date)
        }

    def calculate_rest_days(self, team, date):
        """Calculate days of rest before game"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT MAX(date) FROM game_schedule
            WHERE date < ? AND (home_team = ? OR away_team = ?)
        ''', (date, team, team))

        last_game = cursor.fetchone()

        if last_game and last_game[0]:
            last_game_date = datetime.strptime(last_game[0], '%Y-%m-%d')
            current_date = datetime.strptime(date, '%Y-%m-%d')
            return (current_date - last_game_date).days - 1

        return 2  # Default rest days

    def update_all_data(self):
        """Update all data sources"""
        print("Updating all NBA data...")

        # Fetch latest data
        self.fetch_player_season_stats()
        self.fetch_team_stats()
        self.fetch_injury_report()
        self.fetch_schedule()

        print("Data update complete!")

    def close(self):
        """Close database connection"""
        self.conn.close()

# Advanced analytics functions
class AdvancedAnalytics:
    """
    Advanced statistical analysis for predictions
    """

    @staticmethod
    def calculate_pace_adjustment(team_pace, opponent_pace, league_avg_pace=100.0):
        """Calculate pace adjustment factor"""
        expected_pace = (team_pace + opponent_pace) / 2
        pace_factor = expected_pace / league_avg_pace
        return pace_factor

    @staticmethod
    def calculate_defensive_matchup_rating(position, opp_def_rating, opp_position_defense):
        """Calculate how well opponent defends specific position"""
        base_impact = opp_def_rating / 110  # Normalize to league average
        position_factor = opp_position_defense.get(position, 1.0)
        return base_impact * position_factor

    @staticmethod
    def altitude_impact(arena):
        """Calculate impact of playing at high altitude"""
        high_altitude_arenas = {
            'Denver': 0.03,  # 3% boost for home team
            'Salt Lake City': 0.02,
            'Phoenix': 0.01
        }
        return high_altitude_arenas.get(arena, 0)

    @staticmethod
    def travel_fatigue(origin_city, destination_city):
        """Calculate travel fatigue based on distance"""
        # In production, would use actual distance calculations
        # Simplified version
        coast_to_coast = ['LAL-BOS', 'LAC-BOS', 'GSW-MIA', 'POR-MIA']

        combo = f"{origin_city}-{destination_city}"
        if combo in coast_to_coast:
            return 0.05  # 5% fatigue for coast-to-coast travel

        return 0.02  # Default travel fatigue

if __name__ == "__main__":
    # Initialize data fetcher
    fetcher = NBADataFetcher()

    # Update all data
    fetcher.update_all_data()

    # Example: Get player's recent form
    recent_form = fetcher.get_recent_form('2544', games=5)  # LeBron's ID
    print("Recent form:", recent_form)

    # Check for back-to-back games
    b2b_info = fetcher.get_back_to_back_games('Lakers', '2024-12-15')
    print("Back-to-back info:", b2b_info)

    fetcher.close()
