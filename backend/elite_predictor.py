"""
Elite NBA Prediction Engine with Advanced Analytics
Includes usage rates, defender matchups, teammate injuries, and micro-stats
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from collections import defaultdict
import sqlite3
from advanced_predictor import AdvancedNBAPredictor

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

    def calculate_usage_rate(self, player_name, games=10):
        """
        Calculate player's usage rate
        Usage% = 100 * ((FGA + 0.44 * FTA + TOV) * (Team_Min / 5)) / (Min * (Team_FGA + 0.44 * Team_FTA + Team_TOV))
        Simplified: % of team possessions used when player is on floor
        """
        if player_name in self.usage_cache:
            return self.usage_cache[player_name]

        self.connect_db()

        query = """
            SELECT
                SUM(field_goals_attempted) as fga,
                SUM(free_throws_attempted) as fta,
                SUM(turnovers) as tov,
                SUM(minutes) as min,
                COUNT(*) as games
            FROM player_stats
            WHERE player_name = ?
            ORDER BY date DESC
            LIMIT ?
        """

        df = pd.read_sql_query(query, self.conn, params=(player_name, games))

        if df.empty or df.iloc[0]['games'] == 0:
            return 0.25  # League average ~25%

        row = df.iloc[0]
        player_poss = row['fga'] + (0.44 * row['fta']) + row['tov']
        minutes = row['min']

        if minutes == 0:
            return 0.25

        # Estimate team possessions (simplified)
        # Assume team takes ~90 shots, 20 FTs, 14 TOs per game
        team_poss_per_game = 90 + (0.44 * 20) + 14  # ~113 possessions
        team_poss = team_poss_per_game * row['games']

        # Usage = player possessions / (team possessions * (player minutes / team minutes))
        # Simplified: we don't have exact team data, so estimate
        usage_rate = (player_poss / team_poss) * (240 / minutes)  # 240 = team minutes per game

        # Cap between 10% and 45%
        usage_rate = max(0.10, min(0.45, usage_rate))

        self.usage_cache[player_name] = usage_rate
        return usage_rate

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
        Returns: {usage_boost: float, minutes_boost: float, context: str}
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
                'context': 'Full squad available'
            }

        injured_count = len(df)

        # Each injured key player increases usage by 3-8%
        usage_boost = 1.0 + (injured_count * 0.05)  # 5% per injured teammate
        minutes_boost = 1.0 + (injured_count * 0.03)  # 3% more minutes per injury

        # Cap boosts
        usage_boost = min(1.25, usage_boost)  # Max 25% boost
        minutes_boost = min(1.15, minutes_boost)  # Max 15% more minutes

        injured_names = ', '.join(df['player_name'].tolist()[:3])
        context = f"{injured_count} key player(s) out: {injured_names}"

        return {
            'usage_boost': usage_boost,
            'minutes_boost': minutes_boost,
            'injured_teammates': injured_count,
            'context': context
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

        # Calculate advanced metrics
        usage_rate = self.calculate_usage_rate(player_name)
        ts_percentage = self.calculate_true_shooting_percentage(player_name)

        # Teammate injury analysis
        if player_team:
            teammate_impact = self.analyze_teammate_injuries(player_name, player_team)
        else:
            teammate_impact = {
                'usage_boost': 1.0,
                'minutes_boost': 1.0,
                'injured_teammates': 0,
                'context': 'Team unknown'
            }

        # Defender matchup analysis
        defender_matchup = self.analyze_defender_matchup(player_name, opponent, player_position)

        # Get team paces for pace adjustment
        team_stats = self.get_comprehensive_team_stats(opponent)
        opponent_pace = team_stats.get('pace', 100.0)
        player_team_pace = 100.0  # Default, we'd need player's team stats

        # Apply elite adjustments
        usage_factor = 1.0 + ((usage_rate - 0.25) * 0.3)  # Higher usage = more opportunities
        teammate_usage_boost = teammate_impact['usage_boost']
        teammate_minutes_boost = teammate_impact['minutes_boost']
        defender_factor = defender_matchup['defender_impact']

        # Adjust predictions
        elite_points = base_prediction['points']['prediction'] * usage_factor * teammate_usage_boost * defender_factor
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

        # Add elite factors
        base_prediction['elite_factors'] = {
            'usage_rate': round(usage_rate * 100, 1),  # As percentage
            'true_shooting_pct': round(ts_percentage * 100, 1),
            'teammate_injury_impact': {
                'usage_boost': round(teammate_usage_boost, 3),
                'minutes_boost': round(teammate_minutes_boost, 3),
                'injured_count': teammate_impact['injured_teammates'],
                'context': teammate_impact['context']
            },
            'defender_matchup': {
                'impact': round(defender_factor, 3),
                'difficulty': defender_matchup['matchup_difficulty'],
                'historical': defender_matchup['historical_context']
            },
            'usage_adjustment': round(usage_factor, 3),
            'pace_impact': round((opponent_pace / 100.0), 3)
        }

        # Enhanced analysis
        elite_analysis = []
        elite_analysis.append(f"📊 Usage Rate: {usage_rate*100:.1f}% (League avg ~25%)")

        if usage_rate > 0.30:
            elite_analysis.append("🔥 High usage player - team relies heavily on them")
        elif usage_rate < 0.20:
            elite_analysis.append("📉 Lower usage role - efficient within system")

        if teammate_impact['injured_teammates'] > 0:
            elite_analysis.append(f"⚕️ {teammate_impact['context']}")
            elite_analysis.append(f"   ↑ Expected usage boost: +{(teammate_usage_boost-1)*100:.1f}%")
            elite_analysis.append(f"   ↑ Expected minutes boost: +{(teammate_minutes_boost-1)*100:.1f}%")

        elite_analysis.append(f"🎯 TS%: {ts_percentage*100:.1f}% (Shooting efficiency)")
        elite_analysis.append(f"🛡️ Defender Matchup: {defender_matchup['matchup_difficulty']}")

        if defender_matchup['historical_context'] != "No historical data":
            elite_analysis.append(f"   {defender_matchup['historical_context']}")

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
