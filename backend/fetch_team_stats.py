#!/usr/bin/env python3
"""
Comprehensive Team Statistics Pipeline
Fetches detailed offensive and defensive ratings, pace, and efficiency metrics
"""
import sqlite3
from nba_data_pipeline import NBADataPipeline
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamStatsPipeline(NBADataPipeline):
    """Extended pipeline for comprehensive team statistics"""

    def fetch_team_base_stats(self, season='2024-25'):
        """Fetch base team statistics"""
        logger.info(f"Fetching base team stats for {season}...")

        endpoint = 'leaguedashteamstats'
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
            'GameSegment': '',
            'Period': '0',
            'ShotClockRange': '',
            'LastNGames': '0'
        }

        data = self.make_request(endpoint, params)

        if not data or 'resultSets' not in data:
            logger.error("Failed to fetch base team stats")
            return pd.DataFrame()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers)
        logger.info(f"✓ Fetched base stats for {len(df)} teams")

        return df

    def fetch_team_advanced_stats(self, season='2024-25'):
        """Fetch advanced team statistics (ratings, pace, etc.)"""
        logger.info(f"Fetching advanced team stats for {season}...")

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
            logger.error("Failed to fetch advanced team stats")
            return pd.DataFrame()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers)
        logger.info(f"✓ Fetched advanced stats for {len(df)} teams")

        return df

    def fetch_team_opponent_stats(self, season='2024-25'):
        """Fetch stats about opponent performance (defensive impact)"""
        logger.info(f"Fetching team opponent stats for {season}...")

        endpoint = 'leaguedashteamstats'
        params = {
            'MeasureType': 'Opponent',
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
            logger.error("Failed to fetch opponent stats")
            return pd.DataFrame()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers)
        logger.info(f"✓ Fetched opponent stats for {len(df)} teams")

        return df

    def fetch_team_four_factors(self, season='2024-25'):
        """Fetch four factors stats (eFG%, TOV%, ORB%, FT Rate)"""
        logger.info(f"Fetching team four factors for {season}...")

        endpoint = 'leaguedashteamstats'
        params = {
            'MeasureType': 'Four Factors',
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
            logger.error("Failed to fetch four factors")
            return pd.DataFrame()

        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        df = pd.DataFrame(rows, columns=headers)
        logger.info(f"✓ Fetched four factors for {len(df)} teams")

        return df

    def save_comprehensive_team_stats(self, season='2024-25'):
        """
        Fetch and save comprehensive team statistics
        Combines base, advanced, opponent, and four factors data
        """
        logger.info("=" * 70)
        logger.info("FETCHING COMPREHENSIVE TEAM STATISTICS")
        logger.info("=" * 70)

        self.connect_db()

        try:
            # Fetch all stat types
            base_stats = self.fetch_team_base_stats(season)
            advanced_stats = self.fetch_team_advanced_stats(season)
            opponent_stats = self.fetch_team_opponent_stats(season)
            four_factors = self.fetch_team_four_factors(season)

            # Merge all data
            logger.info("\nMerging all team statistics...")

            # Team abbreviation mapping for full names
            team_full_names = {
                'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets',
                'CHA': 'Charlotte Hornets', 'CHI': 'Chicago Bulls', 'CLE': 'Cleveland Cavaliers',
                'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets', 'DET': 'Detroit Pistons',
                'GSW': 'Golden State Warriors', 'HOU': 'Houston Rockets', 'IND': 'Indiana Pacers',
                'LAC': 'LA Clippers', 'LAL': 'Los Angeles Lakers', 'MEM': 'Memphis Grizzlies',
                'MIA': 'Miami Heat', 'MIL': 'Milwaukee Bucks', 'MIN': 'Minnesota Timberwolves',
                'NOP': 'New Orleans Pelicans', 'NYK': 'New York Knicks', 'OKC': 'Oklahoma City Thunder',
                'ORL': 'Orlando Magic', 'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns',
                'POR': 'Portland Trail Blazers', 'SAC': 'Sacramento Kings', 'SAS': 'San Antonio Spurs',
                'TOR': 'Toronto Raptors', 'UTA': 'Utah Jazz', 'WAS': 'Washington Wizards'
            }

            cursor = self.conn.cursor()

            # Team ID to abbreviation mapping
            team_id_to_abbrev = {
                1610612737: 'ATL', 1610612738: 'BOS', 1610612751: 'BKN', 1610612766: 'CHA',
                1610612741: 'CHI', 1610612739: 'CLE', 1610612742: 'DAL', 1610612743: 'DEN',
                1610612765: 'DET', 1610612744: 'GSW', 1610612745: 'HOU', 1610612754: 'IND',
                1610612746: 'LAC', 1610612747: 'LAL', 1610612763: 'MEM', 1610612748: 'MIA',
                1610612749: 'MIL', 1610612750: 'MIN', 1610612740: 'NOP', 1610612752: 'NYK',
                1610612760: 'OKC', 1610612753: 'ORL', 1610612755: 'PHI', 1610612756: 'PHX',
                1610612757: 'POR', 1610612758: 'SAC', 1610612759: 'SAS', 1610612761: 'TOR',
                1610612762: 'UTA', 1610612764: 'WAS'
            }

            for _, base_row in base_stats.iterrows():
                team_id = str(base_row['TEAM_ID'])
                team_abbrev = team_id_to_abbrev.get(int(team_id), 'UNK')
                team_full_name = team_full_names.get(team_abbrev, base_row.get('TEAM_NAME', team_abbrev))

                # Find corresponding rows in other dataframes
                adv_row = advanced_stats[advanced_stats['TEAM_ID'] == int(team_id)].iloc[0] if not advanced_stats.empty else None
                opp_row = opponent_stats[opponent_stats['TEAM_ID'] == int(team_id)].iloc[0] if not opponent_stats.empty else None
                ff_row = four_factors[four_factors['TEAM_ID'] == int(team_id)].iloc[0] if not four_factors.empty else None

                # Extract all statistics
                wins = base_row.get('W', 0)
                losses = base_row.get('L', 0)

                # Offensive stats
                points_pg = base_row.get('PTS', 0)
                field_goal_pct = base_row.get('FG_PCT', 0)
                three_point_pct = base_row.get('FG3_PCT', 0)
                free_throw_pct = base_row.get('FT_PCT', 0)
                assists_pg = base_row.get('AST', 0)
                rebounds_pg = base_row.get('REB', 0)
                turnovers_pg = base_row.get('TOV', 0)

                # Advanced metrics
                offensive_rating = adv_row.get('OFF_RATING', 0) if adv_row is not None else 0
                defensive_rating = adv_row.get('DEF_RATING', 0) if adv_row is not None else 0
                net_rating = adv_row.get('NET_RATING', 0) if adv_row is not None else 0
                pace = adv_row.get('PACE', 0) if adv_row is not None else 0

                # True shooting and effective field goal
                true_shooting_pct = adv_row.get('TS_PCT', 0) if adv_row is not None else 0
                effective_fg_pct = adv_row.get('EFG_PCT', 0) if adv_row is not None else 0

                # Opponent stats (defensive impact)
                opp_points_pg = opp_row.get('PTS', 0) if opp_row is not None else 0
                opp_fg_pct = opp_row.get('FG_PCT', 0) if opp_row is not None else 0
                opp_three_pct = opp_row.get('FG3_PCT', 0) if opp_row is not None else 0

                # Four factors
                efg_pct = ff_row.get('EFG_PCT', 0) if ff_row is not None else 0
                fta_rate = ff_row.get('FTA_RATE', 0) if ff_row is not None else 0
                tm_tov_pct = ff_row.get('TM_TOV_PCT', 0) if ff_row is not None else 0
                oreb_pct = ff_row.get('OREB_PCT', 0) if ff_row is not None else 0

                # Save to database
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO team_stats (
                            team_id, team_name, season, date,
                            wins, losses, points_pg, field_goal_pct, three_point_pct,
                            free_throw_pct, assists_pg, rebounds_pg, turnovers_pg,
                            offensive_rating, defensive_rating, net_rating, pace,
                            true_shooting_pct, effective_fg_pct,
                            opp_points_pg, opp_fg_pct, opp_three_pct,
                            efg_pct, fta_rate, tm_tov_pct, oreb_pct
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        team_id, team_full_name, season, datetime.now().strftime('%Y-%m-%d'),
                        wins, losses, points_pg, field_goal_pct, three_point_pct,
                        free_throw_pct, assists_pg, rebounds_pg, turnovers_pg,
                        offensive_rating, defensive_rating, net_rating, pace,
                        true_shooting_pct, effective_fg_pct,
                        opp_points_pg, opp_fg_pct, opp_three_pct,
                        efg_pct, fta_rate, tm_tov_pct, oreb_pct
                    ))

                    logger.info(f"  ✓ {team_abbrev}: OFF={offensive_rating:.1f}, DEF={defensive_rating:.1f}, PACE={pace:.1f}")

                except Exception as e:
                    logger.error(f"Error saving {team_abbrev}: {e}")

            self.conn.commit()

            # Print summary
            logger.info("\n" + "=" * 70)
            logger.info("TEAM STATISTICS SUMMARY")
            logger.info("=" * 70)

            cursor.execute("""
                SELECT team_name, offensive_rating, defensive_rating, net_rating, pace
                FROM team_stats
                WHERE season = ?
                ORDER BY net_rating DESC
            """, (season,))

            results = cursor.fetchall()

            logger.info(f"\n{'Team':<30} {'OFF':<8} {'DEF':<8} {'NET':<8} {'PACE':<8}")
            logger.info("-" * 70)

            for team, off, def_rating, net, pace_val in results:
                logger.info(f"{team:<30} {off:<8.1f} {def_rating:<8.1f} {net:<8.1f} {pace_val:<8.1f}")

            logger.info("\n✓ Team statistics updated successfully!")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Error in team stats pipeline: {e}")
            raise
        finally:
            self.close_db()

def update_team_stats_schema():
    """Update database schema to include all new team stats columns"""
    logger.info("Updating team_stats table schema...")

    conn = sqlite3.connect('../database/nba_data.db')
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(team_stats)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Columns we need
    new_columns = {
        'points_pg': 'REAL',
        'field_goal_pct': 'REAL',
        'three_point_pct': 'REAL',
        'free_throw_pct': 'REAL',
        'assists_pg': 'REAL',
        'rebounds_pg': 'REAL',
        'turnovers_pg': 'REAL',
        'true_shooting_pct': 'REAL',
        'effective_fg_pct': 'REAL',
        'opp_points_pg': 'REAL',
        'opp_fg_pct': 'REAL',
        'opp_three_pct': 'REAL',
        'efg_pct': 'REAL',
        'fta_rate': 'REAL',
        'tm_tov_pct': 'REAL',
        'oreb_pct': 'REAL'
    }

    # Add missing columns
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE team_stats ADD COLUMN {col_name} {col_type}")
                logger.info(f"  ✓ Added column: {col_name}")
            except Exception as e:
                logger.warning(f"  ⚠ Column {col_name} might already exist: {e}")

    conn.commit()
    conn.close()
    logger.info("✓ Schema update complete")

if __name__ == '__main__':
    # Update schema first
    update_team_stats_schema()

    # Fetch and save comprehensive team stats
    pipeline = TeamStatsPipeline()
    pipeline.save_comprehensive_team_stats('2024-25')
