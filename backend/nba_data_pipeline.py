"""
NBA Data Pipeline - Fetch Real NBA Player Stats and Team Rosters
Fetches data from official NBA Stats API and other public sources
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import sqlite3
import json
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBADataPipeline:
    """
    Comprehensive NBA data pipeline for fetching:
    - All NBA players and their teams
    - Player statistics (season and game-by-game)
    - Team rosters and statistics
    - Injury reports
    - Game schedules
    """

    def __init__(self, db_path='../database/nba_data.db'):
        self.db_path = db_path
        self.conn = None

        # NBA Stats API base URL
        self.base_url = 'https://stats.nba.com/stats'

        # Required headers for NBA Stats API
        self.headers = {
            'Host': 'stats.nba.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'Connection': 'keep-alive',
            'Referer': 'https://stats.nba.com/',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }

        # Rate limiting
        self.request_delay = 0.6  # 600ms between requests to avoid rate limiting

    def connect_db(self):
        """Connect to database"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            logger.info(f"Connected to database: {self.db_path}")

    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make API request with error handling and rate limiting"""
        url = f"{self.base_url}/{endpoint}"

        try:
            time.sleep(self.request_delay)  # Rate limiting
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {endpoint}: {e}")
            return None

    def fetch_all_players(self, season='2024-25') -> pd.DataFrame:
        """
        Fetch all active NBA players for the current season
        Returns DataFrame with player_id, name, team, position
        """
        logger.info(f"Fetching all players for season {season}...")

        endpoint = 'commonallplayers'
        params = {
            'LeagueID': '00',
            'Season': season,
            'IsOnlyCurrentSeason': '1'
        }

        data = self.make_request(endpoint, params)

        if not data or 'resultSets' not in data:
            logger.error("Failed to fetch players")
            return pd.DataFrame()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers)

        # Keep only active players
        df = df[df['ROSTERSTATUS'] == 1]

        logger.info(f"✓ Fetched {len(df)} active players")
        return df

    def fetch_team_rosters(self, season='2024-25') -> Dict[str, List[Dict]]:
        """
        Fetch complete team rosters (which team has which players)
        Returns dict: {team_abbrev: [list of players]}
        """
        logger.info("Fetching team rosters...")

        # First get all teams
        teams_data = self.fetch_teams(season)
        rosters = {}

        for _, team in teams_data.iterrows():
            team_id = team['TEAM_ID']
            team_abbrev = team['ABBREVIATION']

            logger.info(f"  Fetching roster for {team_abbrev}...")

            endpoint = 'commonteamroster'
            params = {
                'Season': season,
                'TeamID': team_id
            }

            data = self.make_request(endpoint, params)

            if data and 'resultSets' in data and len(data['resultSets']) > 0:
                headers = data['resultSets'][0]['headers']
                rows = data['resultSets'][0]['rowSet']

                roster_df = pd.DataFrame(rows, columns=headers)

                players = []
                for _, player in roster_df.iterrows():
                    players.append({
                        'player_id': str(player['PLAYER_ID']),
                        'name': player['PLAYER'],
                        'number': player.get('NUM', ''),
                        'position': player.get('POSITION', ''),
                        'height': player.get('HEIGHT', ''),
                        'weight': player.get('WEIGHT', ''),
                        'age': player.get('AGE', '')
                    })

                rosters[team_abbrev] = players
                logger.info(f"    ✓ {len(players)} players on {team_abbrev}")

        logger.info(f"✓ Fetched rosters for {len(rosters)} teams")
        return rosters

    def fetch_teams(self, season='2024-25') -> pd.DataFrame:
        """Fetch all NBA teams"""
        logger.info("Fetching NBA teams...")

        # Team abbreviation mapping
        team_abbrev_map = {
            1610612737: 'ATL', 1610612738: 'BOS', 1610612751: 'BKN', 1610612766: 'CHA',
            1610612741: 'CHI', 1610612739: 'CLE', 1610612742: 'DAL', 1610612743: 'DEN',
            1610612765: 'DET', 1610612744: 'GSW', 1610612745: 'HOU', 1610612754: 'IND',
            1610612746: 'LAC', 1610612747: 'LAL', 1610612763: 'MEM', 1610612748: 'MIA',
            1610612749: 'MIL', 1610612750: 'MIN', 1610612740: 'NOP', 1610612752: 'NYK',
            1610612760: 'OKC', 1610612753: 'ORL', 1610612755: 'PHI', 1610612756: 'PHX',
            1610612757: 'POR', 1610612758: 'SAC', 1610612759: 'SAS', 1610612761: 'TOR',
            1610612762: 'UTA', 1610612764: 'WAS'
        }

        # Get current active teams
        endpoint = 'leaguestandings'
        params = {
            'LeagueID': '00',
            'Season': season,
            'SeasonType': 'Regular Season'
        }

        data = self.make_request(endpoint, params)

        if data and 'resultSets' in data:
            headers = data['resultSets'][0]['headers']
            rows = data['resultSets'][0]['rowSet']
            df = pd.DataFrame(rows, columns=headers)

            # Normalize column names to match expected format
            df = df.rename(columns={
                'TeamID': 'TEAM_ID',
                'TeamName': 'TEAM_NAME',
                'TeamCity': 'TEAM_CITY'
            })

            # Add abbreviations
            df['ABBREVIATION'] = df['TEAM_ID'].map(team_abbrev_map)

            logger.info(f"✓ Fetched {len(df)} teams")
            return df

        return self._get_fallback_teams()

    def _get_fallback_teams(self) -> pd.DataFrame:
        """Fallback team list if API fails"""
        teams = [
            {'TEAM_ID': 1610612737, 'TEAM_NAME': 'Atlanta Hawks', 'ABBREVIATION': 'ATL'},
            {'TEAM_ID': 1610612738, 'TEAM_NAME': 'Boston Celtics', 'ABBREVIATION': 'BOS'},
            {'TEAM_ID': 1610612751, 'TEAM_NAME': 'Brooklyn Nets', 'ABBREVIATION': 'BKN'},
            {'TEAM_ID': 1610612766, 'TEAM_NAME': 'Charlotte Hornets', 'ABBREVIATION': 'CHA'},
            {'TEAM_ID': 1610612741, 'TEAM_NAME': 'Chicago Bulls', 'ABBREVIATION': 'CHI'},
            {'TEAM_ID': 1610612739, 'TEAM_NAME': 'Cleveland Cavaliers', 'ABBREVIATION': 'CLE'},
            {'TEAM_ID': 1610612742, 'TEAM_NAME': 'Dallas Mavericks', 'ABBREVIATION': 'DAL'},
            {'TEAM_ID': 1610612743, 'TEAM_NAME': 'Denver Nuggets', 'ABBREVIATION': 'DEN'},
            {'TEAM_ID': 1610612765, 'TEAM_NAME': 'Detroit Pistons', 'ABBREVIATION': 'DET'},
            {'TEAM_ID': 1610612744, 'TEAM_NAME': 'Golden State Warriors', 'ABBREVIATION': 'GSW'},
            {'TEAM_ID': 1610612745, 'TEAM_NAME': 'Houston Rockets', 'ABBREVIATION': 'HOU'},
            {'TEAM_ID': 1610612754, 'TEAM_NAME': 'Indiana Pacers', 'ABBREVIATION': 'IND'},
            {'TEAM_ID': 1610612746, 'TEAM_NAME': 'LA Clippers', 'ABBREVIATION': 'LAC'},
            {'TEAM_ID': 1610612747, 'TEAM_NAME': 'Los Angeles Lakers', 'ABBREVIATION': 'LAL'},
            {'TEAM_ID': 1610612763, 'TEAM_NAME': 'Memphis Grizzlies', 'ABBREVIATION': 'MEM'},
            {'TEAM_ID': 1610612748, 'TEAM_NAME': 'Miami Heat', 'ABBREVIATION': 'MIA'},
            {'TEAM_ID': 1610612749, 'TEAM_NAME': 'Milwaukee Bucks', 'ABBREVIATION': 'MIL'},
            {'TEAM_ID': 1610612750, 'TEAM_NAME': 'Minnesota Timberwolves', 'ABBREVIATION': 'MIN'},
            {'TEAM_ID': 1610612740, 'TEAM_NAME': 'New Orleans Pelicans', 'ABBREVIATION': 'NOP'},
            {'TEAM_ID': 1610612752, 'TEAM_NAME': 'New York Knicks', 'ABBREVIATION': 'NYK'},
            {'TEAM_ID': 1610612760, 'TEAM_NAME': 'Oklahoma City Thunder', 'ABBREVIATION': 'OKC'},
            {'TEAM_ID': 1610612753, 'TEAM_NAME': 'Orlando Magic', 'ABBREVIATION': 'ORL'},
            {'TEAM_ID': 1610612755, 'TEAM_NAME': 'Philadelphia 76ers', 'ABBREVIATION': 'PHI'},
            {'TEAM_ID': 1610612756, 'TEAM_NAME': 'Phoenix Suns', 'ABBREVIATION': 'PHX'},
            {'TEAM_ID': 1610612757, 'TEAM_NAME': 'Portland Trail Blazers', 'ABBREVIATION': 'POR'},
            {'TEAM_ID': 1610612758, 'TEAM_NAME': 'Sacramento Kings', 'ABBREVIATION': 'SAC'},
            {'TEAM_ID': 1610612759, 'TEAM_NAME': 'San Antonio Spurs', 'ABBREVIATION': 'SAS'},
            {'TEAM_ID': 1610612761, 'TEAM_NAME': 'Toronto Raptors', 'ABBREVIATION': 'TOR'},
            {'TEAM_ID': 1610612762, 'TEAM_NAME': 'Utah Jazz', 'ABBREVIATION': 'UTA'},
            {'TEAM_ID': 1610612764, 'TEAM_NAME': 'Washington Wizards', 'ABBREVIATION': 'WAS'},
        ]
        return pd.DataFrame(teams)

    def fetch_player_season_stats(self, season='2024-25') -> pd.DataFrame:
        """Fetch season averages for all players"""
        logger.info(f"Fetching player season stats for {season}...")

        endpoint = 'leaguedashplayerstats'
        params = {
            'MeasureType': 'Base',
            'PerMode': 'PerGame',
            'PlusMinus': 'N',
            'PaceAdjust': 'N',
            'Rank': 'N',
            'LeagueID': '00',
            'Season': season,
            'SeasonType': 'Regular Season',
            'PORound': '0',
            'Outcome': '',
            'Location': '',
            'Month': '0',
            'SeasonSegment': '',
            'DateFrom': '',
            'DateTo': '',
            'OpponentTeamID': '0',
            'VsConference': '',
            'VsDivision': '',
            'TeamID': '0',
            'Conference': '',
            'Division': '',
            'GameSegment': '',
            'Period': '0',
            'ShotClockRange': '',
            'LastNGames': '0'
        }

        data = self.make_request(endpoint, params)

        if not data or 'resultSets' not in data:
            logger.error("Failed to fetch season stats")
            return pd.DataFrame()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers)
        logger.info(f"✓ Fetched stats for {len(df)} players")

        return df

    def fetch_player_game_logs(self, player_id: str, season='2024-25') -> pd.DataFrame:
        """Fetch game-by-game stats for a specific player"""
        logger.info(f"Fetching game logs for player {player_id}...")

        endpoint = 'playergamelog'
        params = {
            'PlayerID': player_id,
            'Season': season,
            'SeasonType': 'Regular Season'
        }

        data = self.make_request(endpoint, params)

        if not data or 'resultSets' not in data:
            return pd.DataFrame()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        return pd.DataFrame(rows, columns=headers)

    def fetch_team_stats(self, season='2024-25') -> pd.DataFrame:
        """Fetch team statistics including defensive ratings"""
        logger.info(f"Fetching team stats for {season}...")

        endpoint = 'leaguedashteamstats'
        params = {
            'MeasureType': 'Advanced',
            'PerMode': 'PerGame',
            'PlusMinus': 'N',
            'PaceAdjust': 'N',
            'Rank': 'N',
            'LeagueID': '00',
            'Season': season,
            'SeasonType': 'Regular Season',
            'PORound': '0',
            'Outcome': '',
            'Location': '',
            'Month': '0',
            'SeasonSegment': '',
            'DateFrom': '',
            'DateTo': '',
            'OpponentTeamID': '0',
            'VsConference': '',
            'VsDivision': '',
            'GameSegment': '',
            'Period': '0',
            'ShotClockRange': '',
            'LastNGames': '0'
        }

        data = self.make_request(endpoint, params)

        if not data or 'resultSets' not in data:
            logger.error("Failed to fetch team stats")
            return pd.DataFrame()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers)
        logger.info(f"✓ Fetched stats for {len(df)} teams")

        return df

    def save_to_database(self):
        """
        Main pipeline function - Fetch and save all data to database
        """
        logger.info("=" * 70)
        logger.info("STARTING NBA DATA PIPELINE")
        logger.info("=" * 70)

        self.connect_db()

        try:
            # 1. Fetch and save team rosters
            logger.info("\n[1/5] Fetching team rosters...")
            rosters = self.fetch_team_rosters()
            self._save_rosters_to_db(rosters)

            # 2. Fetch and save player season stats
            logger.info("\n[2/5] Fetching player season stats...")
            season_stats = self.fetch_player_season_stats()
            self._save_season_stats_to_db(season_stats)

            # 3. Fetch and save team stats
            logger.info("\n[3/5] Fetching team stats...")
            team_stats = self.fetch_team_stats()
            self._save_team_stats_to_db(team_stats)

            # 4. Fetch game logs for top players (sample)
            logger.info("\n[4/5] Fetching game logs for key players...")
            self._fetch_and_save_game_logs(season_stats.head(50))  # Top 50 players

            # 5. Summary
            logger.info("\n[5/5] Pipeline Summary:")
            self._print_summary()

            logger.info("\n" + "=" * 70)
            logger.info("✓ NBA DATA PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
        finally:
            self.close_db()

    def _save_rosters_to_db(self, rosters: Dict):
        """Save team rosters to database"""
        cursor = self.conn.cursor()

        for team, players in rosters.items():
            for player in players:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO player_season_stats
                        (player_id, player_name, team, season)
                        VALUES (?, ?, ?, ?)
                    """, (player['player_id'], player['name'], team, '2024-25'))
                except Exception as e:
                    logger.warning(f"Error saving player {player['name']}: {e}")

        self.conn.commit()
        logger.info(f"  ✓ Saved rosters to database")

    def _save_season_stats_to_db(self, df: pd.DataFrame):
        """Save player season statistics"""
        if df.empty:
            return

        cursor = self.conn.cursor()

        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_season_stats
                    (player_id, player_name, team, season, games_played,
                     minutes_avg, points_avg, rebounds_avg, assists_avg,
                     steals_avg, blocks_avg, turnovers_avg,
                     field_goal_pct, three_point_pct, free_throw_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['PLAYER_ID']), row['PLAYER_NAME'], row['TEAM_ABBREVIATION'],
                    '2024-25', row.get('GP', 0),
                    row.get('MIN', 0), row.get('PTS', 0), row.get('REB', 0),
                    row.get('AST', 0), row.get('STL', 0), row.get('BLK', 0),
                    row.get('TOV', 0), row.get('FG_PCT', 0),
                    row.get('FG3_PCT', 0), row.get('FT_PCT', 0)
                ))
            except Exception as e:
                logger.warning(f"Error saving stats for {row.get('PLAYER_NAME', 'Unknown')}: {e}")

        self.conn.commit()
        logger.info(f"  ✓ Saved season stats for {len(df)} players")

    def _save_team_stats_to_db(self, df: pd.DataFrame):
        """Save team statistics"""
        if df.empty:
            return

        cursor = self.conn.cursor()

        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO team_stats
                    (team_id, team_name, season, date, wins, losses,
                     offensive_rating, defensive_rating, net_rating, pace)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['TEAM_ID']), row['TEAM_NAME'], '2024-25',
                    datetime.now().strftime('%Y-%m-%d'),
                    row.get('W', 0), row.get('L', 0),
                    row.get('OFF_RATING', 0), row.get('DEF_RATING', 0),
                    row.get('NET_RATING', 0), row.get('PACE', 0)
                ))
            except Exception as e:
                logger.warning(f"Error saving team stats: {e}")

        self.conn.commit()
        logger.info(f"  ✓ Saved stats for {len(df)} teams")

    def _fetch_and_save_game_logs(self, players_df: pd.DataFrame):
        """Fetch and save game logs for top players"""
        cursor = self.conn.cursor()
        count = 0

        for _, player in players_df.iterrows():
            player_id = str(player['PLAYER_ID'])
            player_name = player['PLAYER_NAME']
            team = player['TEAM_ABBREVIATION']

            logger.info(f"  Fetching games for {player_name}...")

            game_logs = self.fetch_player_game_logs(player_id)

            if game_logs.empty:
                continue

            for _, game in game_logs.iterrows():
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO player_stats
                        (player_id, player_name, team, date, opponent, is_home,
                         minutes, points, rebounds, assists, steals, blocks, turnovers,
                         field_goals_made, field_goals_attempted,
                         three_pointers_made, three_pointers_attempted,
                         free_throws_made, free_throws_attempted, plus_minus)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        player_id, player_name, team,
                        game.get('GAME_DATE', ''), game.get('MATCHUP', '').split()[-1],
                        'vs' in game.get('MATCHUP', ''),
                        game.get('MIN', 0), game.get('PTS', 0), game.get('REB', 0),
                        game.get('AST', 0), game.get('STL', 0), game.get('BLK', 0),
                        game.get('TOV', 0), game.get('FGM', 0), game.get('FGA', 0),
                        game.get('FG3M', 0), game.get('FG3A', 0),
                        game.get('FTM', 0), game.get('FTA', 0), game.get('PLUS_MINUS', 0)
                    ))
                except Exception as e:
                    logger.warning(f"Error saving game: {e}")

            count += 1
            self.conn.commit()

        logger.info(f"  ✓ Saved game logs for {count} players")

    def _print_summary(self):
        """Print database summary"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM player_season_stats")
        player_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM player_stats")
        game_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM team_stats")
        team_count = cursor.fetchone()[0]

        logger.info(f"  Total players in database: {player_count}")
        logger.info(f"  Total game records: {game_count}")
        logger.info(f"  Total teams: {team_count}")


if __name__ == "__main__":
    pipeline = NBADataPipeline()
    pipeline.save_to_database()
