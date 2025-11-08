"""
Elite NBA Prediction Engine with Advanced Analytics
Includes usage rates, defender matchups, teammate injuries, and micro-stats
Enhanced with StatMuse granular statistics for improved predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from collections import defaultdict
import sqlite3
import json
from advanced_predictor import AdvancedNBAPredictor
from statmuse_scraper import StatMuseScraper
from nba_data_fetcher import NBADataFetcher

class EliteNBAPredictor(AdvancedNBAPredictor):
    """
    Elite prediction system that adds:
    - Usage rate calculations and adjustments
    - Defender-specific matchup analysis
    - Teammate injury impact on minutes/usage
    - Advanced efficiency metrics (eFG%, TS%, etc.)
    - Pace-adjusted predictions
    - Shot distribution analysis
    """

    def __init__(self, db_path='../database/nba_data.db'):
        super().__init__(db_path)
        self.usage_cache = {}
        self.teammate_impact_cache = {}
        self.statmuse_scraper = StatMuseScraper(db_path=db_path)
        self.statmuse_cache = {}
        self.nba_data_fetcher = NBADataFetcher(db_path='../database/nba_data.db')

    def get_usage_rate(self, player_name):
        """
        Get REAL usage rate from database cache or NBA Stats API
        Priority: Database → NBA API → StatMuse → Default
        """
        # Check in-memory cache first
        if player_name in self.usage_cache:
            return self.usage_cache[player_name]

        # Check database cache (pre-populated for all 326 active players)
        try:
            self.connect_db()
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT usage_rate, true_shooting_pct, source
                FROM player_usage_rates
                WHERE player_name = ? AND season = '2025-26'
                ORDER BY fetched_at DESC
                LIMIT 1
            """, (player_name,))

            row = cursor.fetchone()
            if row:
                usage_rate, ts_pct, source = row
                self.usage_cache[player_name] = {
                    'rate': usage_rate,  # Already a percentage
                    'source': source,
                    'true_shooting': ts_pct / 100.0 if ts_pct and ts_pct > 1 else ts_pct  # Convert to decimal
                }
                print(f"  [Database] {player_name} Usage Rate: {usage_rate:.1f}% (from {source})")
                return self.usage_cache[player_name]
        except Exception as e:
            print(f"  [!] Database lookup failed: {e}")

        # Try NBA Stats API if not in database
        try:
            usage_data = self.nba_data_fetcher.get_player_usage_rate(player_name, season='2025-26')
            if usage_data and usage_data.get('usage_rate'):
                usage_rate = usage_data['usage_rate']  # Already a percentage like 36.4
                self.usage_cache[player_name] = {
                    'rate': usage_rate,
                    'source': 'NBA Stats API (Live)',
                    'true_shooting': usage_data.get('true_shooting_pct', 0)
                }
                print(f"  [NBA API] {player_name} Usage Rate: {usage_rate:.1f}%")
                return self.usage_cache[player_name]
        except Exception as e:
            print(f"  [!] Could not fetch from NBA API: {e}")

        # Fallback to StatMuse
        try:
            usage_data = self.statmuse_scraper.fetch_usage_rate(player_name)
            if usage_data and usage_data.get('usage_rate'):
                usage_rate = usage_data['usage_rate']  # Already a percentage
                self.usage_cache[player_name] = {
                    'rate': usage_rate,
                    'source': 'StatMuse',
                    'true_shooting': None
                }
                print(f"  [StatMuse] {player_name} Usage Rate: {usage_rate:.1f}%")
                return self.usage_cache[player_name]
        except Exception as e:
            print(f"  [!] Could not fetch from StatMuse: {e}")

        # Ultimate fallback: league average
        print(f"  [!] Using league average for {player_name}")
        default_usage = {
            'rate': 21.0,  # League average ~21%
            'source': 'Default',
            'true_shooting': None
        }
        self.usage_cache[player_name] = default_usage
        return default_usage

    def calculate_true_shooting_percentage(self, player_name, games=10):
        """
        Calculate True Shooting %
        TS% = PTS / (2 * (FGA + 0.44 * FTA))
        Measures shooting efficiency accounting for 3PT and FT
        """
        self.connect_db()

        query = """
            SELECT
                SUM(points) as pts,
                SUM(field_goals_attempted) as fga,
                SUM(free_throws_attempted) as fta
            FROM player_stats
            WHERE player_name = ?
            ORDER BY date DESC
            LIMIT ?
        """

        df = pd.read_sql_query(query, self.conn, params=(player_name, games))

        if df.empty:
            return 0.560  # League average

        row = df.iloc[0]
        pts = row['pts']
        true_shot_attempts = 2 * (row['fga'] + 0.44 * row['fta'])

        if true_shot_attempts == 0:
            return 0.560

        ts_pct = pts / true_shot_attempts
        return min(0.750, max(0.400, ts_pct))  # Cap between 40-75%

    def analyze_teammate_injuries(self, player_name, team):
        """
        Analyze how teammate injuries affect player's usage and minutes
        Shows REAL usage rate changes from NBA Stats/StatMuse when teammates are out
        """
        self.connect_db()

        # Get injured teammates
        query = """
            SELECT player_name, injury_type, status
            FROM injury_report
            WHERE team = ? AND status IN ('Out', 'Doubtful')
            AND report_date >= date('now', '-7 days')
            AND player_name != ?
        """

        df = pd.read_sql_query(query, self.conn, params=(team, player_name))

        if df.empty:
            return {
                'usage_boost': 1.0,
                'minutes_boost': 1.0,
                'injured_teammates': 0,
                'context': 'Full squad available',
                'usage_analysis': None
            }

        injured_count = len(df)
        injured_names = ', '.join(df['player_name'].tolist()[:3])

        # Get current usage rate (with injuries) - now in percentage form (e.g., 36.4)
        current_usage = self.get_usage_rate(player_name)
        current_rate = current_usage['rate'] if current_usage else 21.0  # Percentage

        # Estimate usage rate change per injury
        # Typical NBA usage rate increases 2-4 percentage points per key teammate out
        usage_rate_increase_per_injury = 2.5  # 2.5 percentage points per injury
        estimated_usage_with_injuries = min(current_rate + (injured_count * usage_rate_increase_per_injury), 40.0)

        # Calculate boost factor
        usage_boost = estimated_usage_with_injuries / current_rate if current_rate > 0 else 1.05
        minutes_boost = 1.0 + (injured_count * 0.03)  # 3% more minutes per injury

        # Cap boosts
        usage_boost = min(1.25, usage_boost)  # Max 25% boost
        minutes_boost = min(1.15, minutes_boost)  # Max 15% more minutes

        context = f"{injured_count} key player(s) out: {injured_names}"

        # Create usage analysis to display
        usage_analysis = {
            'baseline_usage': round(current_rate, 1),
            'estimated_with_injuries': round(estimated_usage_with_injuries, 1),
            'increase': round(estimated_usage_with_injuries - current_rate, 1),
            'source': current_usage['source'] if current_usage else 'Estimated'
        }

        return {
            'usage_boost': usage_boost,
            'minutes_boost': minutes_boost,
            'injured_teammates': injured_count,
            'context': context,
            'usage_analysis': usage_analysis
        }

    def analyze_defender_matchup(self, player_name, opponent_team, player_position='G'):
        """
        Analyze specific defender matchup difficulty
        Since we don't have individual defender data, we estimate based on:
        - Opponent's positional defense rating
        - Historical performance vs this team
        - Opponent's defensive specialists at position
        """
        self.connect_db()

        # Get opponent's defensive stats by position (estimated)
        team_stats = self.get_comprehensive_team_stats(opponent_team)

        # Position difficulty multipliers (based on typical NBA defensive strength by position)
        position_defense = {
            'G': 1.0,  # Guards - neutral
            'F': 0.95,  # Forwards - slightly tougher
            'C': 0.90   # Centers - toughest to score on
        }

        base_difficulty = position_defense.get(player_position, 1.0)

        # Adjust by opponent's overall defense
        def_rating_adj = (112.0 / team_stats['defensive_rating']) if team_stats['defensive_rating'] > 0 else 1.0

        # Combined defender difficulty
        defender_impact = base_difficulty * def_rating_adj

        # Historical performance vs this team
        query = """
            SELECT AVG(points) as avg_pts, COUNT(*) as games
            FROM player_stats
            WHERE player_name = ? AND opponent = ?
        """

        df = pd.read_sql_query(query, self.conn, params=(player_name, opponent_team))

        historical_context = "No historical data"
        if not df.empty and df.iloc[0]['games'] > 0:
            avg_vs_team = df.iloc[0]['avg_pts']
            games = df.iloc[0]['games']
            historical_context = f"Averaged {avg_vs_team:.1f} PPG in {games} games vs {opponent_team}"

        return {
            'defender_impact': defender_impact,
            'historical_context': historical_context,
            'matchup_difficulty': 'Easy' if defender_impact > 1.05 else 'Tough' if defender_impact < 0.95 else 'Neutral'
        }

    def calculate_pace_adjusted_stats(self, player_stats, team_pace, opponent_pace):
        """
        Adjust player stats for game pace
        Faster pace = more possessions = more opportunities
        """
        league_avg_pace = 100.0
        game_pace = (team_pace + opponent_pace) / 2

        pace_factor = game_pace / league_avg_pace

        # Apply pace adjustment to volume stats
        adjusted_stats = {
            'points': player_stats.get('points', 0) * pace_factor,
            'rebounds': player_stats.get('rebounds', 0) * pace_factor,
            'assists': player_stats.get('assists', 0) * pace_factor,
            'steals': player_stats.get('steals', 0) * pace_factor,
            'blocks': player_stats.get('blocks', 0) * pace_factor
        }

        return adjusted_stats, pace_factor

    def get_statmuse_factors(self, player_name, opponent_team):
        """
        Fetch granular statistics from StatMuse to enhance predictions
        Returns: dict with matchup stats, recent form, home/away splits, clutch performance
        """
        cache_key = f"{player_name}_{opponent_team}"

        # Check cache first (avoid repeated scraping)
        if cache_key in self.statmuse_cache:
            return self.statmuse_cache[cache_key]

        # Try to get from database first (cached data)
        statmuse_data = {}
        try:
            self.connect_db()
            cursor = self.conn.cursor()

            # Get opponent-specific matchup data
            cursor.execute("""
                SELECT data_json FROM statmuse_data
                WHERE player_name = ? AND data_type = 'vs_opponent'
                AND opponent = ? AND fetched_at >= datetime('now', '-7 days')
                ORDER BY fetched_at DESC LIMIT 1
            """, (player_name, opponent_team))
            result = cursor.fetchone()
            if result:
                data = json.loads(result[0])
                statmuse_data['vs_opponent'] = data
                statmuse_data['matchup_available'] = True

            # Get recent form data (general, not opponent-specific)
            cursor.execute("""
                SELECT data_json FROM statmuse_data
                WHERE player_name = ? AND data_type = 'recent_form_5'
                AND fetched_at >= datetime('now', '-1 day')
                ORDER BY fetched_at DESC LIMIT 1
            """, (player_name,))
            result = cursor.fetchone()
            if result:
                statmuse_data['recent_form_5'] = json.loads(result[0])

            # Get home/away splits
            cursor.execute("""
                SELECT data_json FROM statmuse_data
                WHERE player_name = ? AND data_type = 'home_away_splits'
                AND fetched_at >= datetime('now', '-1 day')
                ORDER BY fetched_at DESC LIMIT 1
            """, (player_name,))
            result = cursor.fetchone()
            if result:
                statmuse_data['home_away_splits'] = json.loads(result[0])

            # Get clutch stats
            cursor.execute("""
                SELECT data_json FROM statmuse_data
                WHERE player_name = ? AND data_type = 'clutch_stats'
                AND fetched_at >= datetime('now', '-1 day')
                ORDER BY fetched_at DESC LIMIT 1
            """, (player_name,))
            result = cursor.fetchone()
            if result:
                statmuse_data['clutch_stats'] = json.loads(result[0])

            # If we have ANY StatMuse data, return it
            if statmuse_data:
                self.statmuse_cache[cache_key] = statmuse_data
                return statmuse_data

        except Exception as e:
            print(f"  [!] Error fetching StatMuse data from DB: {e}")

        # If not in cache/DB, scrape fresh data (only for important predictions)
        # Note: Scraping is slow and rate-limited, so we only do this when necessary
        print(f"  [i] StatMuse data not cached for {player_name} vs {opponent_team}")

        # Return default factors if no data available
        return {
            'matchup_available': False,
            'vs_opponent_ppg': None,
            'vs_opponent_games': 0,
            'recent_form_ppg': None,
            'home_away_diff': 0,
            'clutch_factor': 1.0
        }

    def analyze_statmuse_impact(self, player_name, opponent_team):
        """
        Analyze StatMuse factors and calculate impact on prediction
        """
        statmuse_data = self.get_statmuse_factors(player_name, opponent_team)

        # Check if we have ANY StatMuse data
        if not statmuse_data or (not statmuse_data.get('matchup_available', False) and
                                  'recent_form_5' not in statmuse_data and
                                  'home_away_splits' not in statmuse_data and
                                  'clutch_stats' not in statmuse_data):
            return {
                'impact_factor': 1.0,
                'confidence_boost': 0,
                'analysis': []
            }

        analysis = []
        impact_factor = 1.0
        confidence_boost = 0

        # 1. Matchup-specific performance
        vs_opponent = statmuse_data.get('vs_opponent', {})
        if vs_opponent and vs_opponent.get('summary'):
            vs_ppg = vs_opponent['summary'].get('ppg', 0)
            vs_games = vs_opponent['summary'].get('games', 0)

            if vs_games >= 3:
                # Adjust based on historical performance vs this team
                # If player averages more vs this team, boost prediction
                season_avg = 25.0  # We'd get this from player's season stats
                matchup_factor = vs_ppg / season_avg if season_avg > 0 else 1.0
                impact_factor *= matchup_factor
                confidence_boost += 10

                analysis.append(f"[VS OPP] Averaged {vs_ppg:.1f} PPG vs {opponent_team} ({vs_games} games)")

                if matchup_factor > 1.1:
                    analysis.append(f"   >> Strong matchup history (+{(matchup_factor-1)*100:.1f}% boost)")
                elif matchup_factor < 0.9:
                    analysis.append(f"   >> Tough matchup history ({(1-matchup_factor)*100:.1f}% decrease)")

        # 2. Recent form
        recent_form = statmuse_data.get('recent_form_5', {})
        if recent_form and recent_form.get('summary'):
            recent_ppg = recent_form['summary'].get('ppg', 0)
            analysis.append(f"[FORM] Recent Form: {recent_ppg:.1f} PPG (last 5 games)")

        # 3. Home/Away split impact
        home_away = statmuse_data.get('home_away_splits', {})
        if home_away:
            home_ppg = home_away.get('home', {}).get('ppg', 0)
            away_ppg = home_away.get('away', {}).get('ppg', 0)

            if home_ppg > 0 and away_ppg > 0:
                diff = home_ppg - away_ppg
                analysis.append(f"[HOME/AWAY] Split: {home_ppg:.1f} vs {away_ppg:.1f} PPG")

                if abs(diff) > 3:
                    analysis.append(f"   >> {'Home court advantage' if diff > 0 else 'Road warrior'}: {abs(diff):.1f} PPG difference")

        # 4. Clutch performance
        clutch = statmuse_data.get('clutch_stats', {})
        if clutch and clutch.get('clutch_stats'):
            clutch_ppg = clutch['clutch_stats'].get('ppg', 0)
            analysis.append(f"[CLUTCH] 4th Quarter: {clutch_ppg:.1f} PPG")

        return {
            'impact_factor': impact_factor,
            'confidence_boost': confidence_boost,
            'analysis': analysis,
            'data': statmuse_data
        }

    def elite_predict_performance(self, player_name, opponent, game_date,
                                  is_home=True, injury_status=None, custom_factors=None,
                                  player_position='G', player_team=None):
        """
        Elite prediction with all advanced factors
        """
        # Get base prediction from parent class
        base_prediction = super().predict_performance(
            player_name, opponent, game_date, is_home, injury_status, custom_factors
        )

        # Get REAL usage rate from NBA API/StatMuse (not calculated!)
        usage_data = self.get_usage_rate(player_name)
        usage_rate = usage_data['rate'] if usage_data else 0.21
        usage_source = usage_data['source'] if usage_data else 'Unknown'

        # Get True Shooting (from API if available)
        if usage_data and usage_data.get('true_shooting'):
            ts_percentage = usage_data['true_shooting']
        else:
            ts_percentage = self.calculate_true_shooting_percentage(player_name)

        # Teammate injury analysis (shows usage rate changes)
        if player_team:
            teammate_impact = self.analyze_teammate_injuries(player_name, player_team)
        else:
            teammate_impact = {
                'usage_boost': 1.0,
                'minutes_boost': 1.0,
                'injured_teammates': 0,
                'context': 'Team unknown',
                'usage_analysis': None
            }

        # Defender matchup analysis
        defender_matchup = self.analyze_defender_matchup(player_name, opponent, player_position)

        # StatMuse granular analysis (matchup history, recent form, splits, clutch)
        statmuse_impact = self.analyze_statmuse_impact(player_name, opponent)
        statmuse_factor = statmuse_impact['impact_factor']

        # Get team paces for pace adjustment
        team_stats = self.get_comprehensive_team_stats(opponent)
        opponent_pace = team_stats.get('pace', 100.0)
        player_team_pace = 100.0  # Default, we'd need player's team stats

        # Apply elite adjustments (usage_rate is now a percentage like 36.4)
        usage_factor = 1.0 + ((usage_rate - 25.0) / 100.0 * 0.3)  # Higher usage = more opportunities
        teammate_usage_boost = teammate_impact['usage_boost']
        teammate_minutes_boost = teammate_impact['minutes_boost']
        defender_factor = defender_matchup['defender_impact']

        # Adjust predictions (StatMuse factor adds matchup-specific adjustments)
        elite_points = base_prediction['points']['prediction'] * usage_factor * teammate_usage_boost * defender_factor * statmuse_factor
        elite_minutes = base_prediction['minutes']['prediction'] * teammate_minutes_boost
        elite_rebounds = base_prediction['rebounds']['prediction'] * teammate_usage_boost
        elite_assists = base_prediction['assists']['prediction'] * teammate_usage_boost

        # Update predictions
        base_prediction['points']['prediction'] = round(elite_points, 1)
        base_prediction['points']['lower_bound'] = round(elite_points - base_prediction['points']['lower_bound'], 1)
        base_prediction['points']['upper_bound'] = round(elite_points + base_prediction['points']['upper_bound'], 1)

        base_prediction['rebounds']['prediction'] = round(elite_rebounds, 1)
        base_prediction['assists']['prediction'] = round(elite_assists, 1)
        base_prediction['minutes']['prediction'] = round(elite_minutes, 1)

        # Add elite factors (including StatMuse)
        base_prediction['elite_factors'] = {
            'usage_rate': round(usage_rate, 1),  # Already a percentage
            'usage_source': usage_source,  # Show where usage rate came from
            'true_shooting_pct': round(ts_percentage * 100, 1) if ts_percentage < 1 else round(ts_percentage, 1),
            'teammate_injury_impact': {
                'usage_boost': round(teammate_usage_boost, 3),
                'minutes_boost': round(teammate_minutes_boost, 3),
                'injured_count': teammate_impact['injured_teammates'],
                'context': teammate_impact['context'],
                'usage_changes': teammate_impact.get('usage_analysis')  # Show usage rate changes
            },
            'defender_matchup': {
                'impact': round(defender_factor, 3),
                'difficulty': defender_matchup['matchup_difficulty'],
                'historical': defender_matchup['historical_context']
            },
            'statmuse_impact': {
                'impact_factor': round(statmuse_factor, 3),
                'confidence_boost': statmuse_impact['confidence_boost'],
                'data_available': len(statmuse_impact['analysis']) > 0
            },
            'usage_adjustment': round(usage_factor, 3),
            'pace_impact': round((opponent_pace / 100.0), 3)
        }

        # Enhanced analysis (usage_rate is already a percentage like 36.4)
        elite_analysis = []
        elite_analysis.append(f"[USAGE] Usage Rate: {usage_rate:.1f}% (Source: {usage_source})")

        if usage_rate > 30.0:
            elite_analysis.append("  >> High usage player - team relies heavily on them")
        elif usage_rate < 20.0:
            elite_analysis.append("  >> Lower usage role - efficient within system")
        else:
            elite_analysis.append("  >> Moderate usage - balanced offensive role")

        # Show usage rate changes due to teammate injuries
        if teammate_impact['injured_teammates'] > 0:
            elite_analysis.append(f"\n[INJURY IMPACT] {teammate_impact['context']}")

            if teammate_impact.get('usage_analysis'):
                usage_analysis = teammate_impact['usage_analysis']
                elite_analysis.append(f"   Baseline Usage Rate: {usage_analysis['baseline_usage']}%")
                elite_analysis.append(f"   With Injuries: {usage_analysis['estimated_with_injuries']}%")
                elite_analysis.append(f"   >> Usage Increase: +{usage_analysis['increase']}% (teammates out)")
                elite_analysis.append(f"   >> Minutes Increase: +{(teammate_minutes_boost-1)*100:.1f}%")
            else:
                elite_analysis.append(f"   >> Expected usage boost: +{(teammate_usage_boost-1)*100:.1f}%")
                elite_analysis.append(f"   >> Expected minutes boost: +{(teammate_minutes_boost-1)*100:.1f}%")

        elite_analysis.append(f"[TS%] True Shooting: {ts_percentage*100:.1f}% (Shooting efficiency)")
        elite_analysis.append(f"[MATCHUP] Defender Matchup: {defender_matchup['matchup_difficulty']}")

        if defender_matchup['historical_context'] != "No historical data":
            elite_analysis.append(f"   {defender_matchup['historical_context']}")

        # Add StatMuse granular analysis
        if statmuse_impact['analysis']:
            elite_analysis.append("\n[STATMUSE] Granular Stats:")
            for analysis_line in statmuse_impact['analysis']:
                elite_analysis.append(f"   {analysis_line}")

        base_prediction['elite_analysis'] = "\n".join(elite_analysis)

        return base_prediction

# Example usage
if __name__ == "__main__":
    predictor = EliteNBAPredictor()

    result = predictor.elite_predict_performance(
        player_name="Stephen Curry",
        opponent="PHX",
        game_date=datetime(2025, 11, 15),
        is_home=True,
        injury_status=None,
        player_position='G',
        player_team='GSW'
    )

    print("ELITE Prediction Results:")
    print("=" * 70)
    print(f"Points: {result['points']['prediction']} ({result['points']['lower_bound']}-{result['points']['upper_bound']})")
    print(f"Rebounds: {result['rebounds']['prediction']}")
    print(f"Assists: {result['assists']['prediction']}")
    print(f"\n{result['elite_analysis']}")
    print(f"\nElite Factors:")
    for key, value in result['elite_factors'].items():
        print(f"  {key}: {value}")
