"""
Advanced NBA Prediction Engine with Probability Calculations
Calculates actual probabilities based on historical data, matchups, and defensive analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from collections import defaultdict
import sqlite3

class AdvancedNBAPredictor:
    """
    Advanced prediction system that calculates probabilities based on:
    - Historical performance vs specific teams
    - Defensive matchup ratings
    - Opponent injury status impact
    - Statistical probability distributions
    - Recent form and trends
    """

    def __init__(self, db_path='../database/nba_data.db'):
        self.db_path = db_path
        self.conn = None
        self.player_averages = {}
        self.team_def_ratings = {}
        self.matchup_history = {}

    def connect_db(self):
        """Connect to database"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)

    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_player_vs_team_history(self, player_name, opponent_team, limit=10):
        """
        Get player's historical performance against specific team
        Returns actual game statistics for probability calculation
        """
        self.connect_db()

        query = """
            SELECT date, opponent, points, rebounds, assists, minutes,
                   field_goals_made, field_goals_attempted,
                   three_pointers_made, three_pointers_attempted,
                   steals, blocks, turnovers
            FROM player_stats
            WHERE player_name = ? AND opponent = ?
            ORDER BY date DESC
            LIMIT ?
        """

        df = pd.read_sql_query(query, self.conn, params=(player_name, opponent_team, limit))

        if df.empty:
            # If no direct matchup data, get general stats
            return self.get_player_season_average(player_name)

        return df

    def get_player_season_average(self, player_name, games=20):
        """Get player's season averages"""
        self.connect_db()

        query = """
            SELECT points, rebounds, assists, steals, blocks, turnovers, minutes
            FROM player_stats
            WHERE player_name = ?
            ORDER BY date DESC
            LIMIT ?
        """

        df = pd.read_sql_query(query, self.conn, params=(player_name, games))

        if df.empty:
            # Return default averages if no data
            return {
                'avg_points': 15.0,
                'avg_rebounds': 5.0,
                'avg_assists': 4.0,
                'avg_steals': 1.0,
                'avg_blocks': 0.5,
                'avg_turnovers': 2.0,
                'avg_minutes': 30.0,
                'std_points': 5.0,
                'std_rebounds': 2.0,
                'std_assists': 2.0
            }

        # Calculate averages and standard deviations in Python
        result = {
            'avg_points': df['points'].mean(),
            'avg_rebounds': df['rebounds'].mean(),
            'avg_assists': df['assists'].mean(),
            'avg_steals': df['steals'].mean(),
            'avg_blocks': df['blocks'].mean(),
            'avg_turnovers': df['turnovers'].mean(),
            'avg_minutes': df['minutes'].mean(),
            'std_points': df['points'].std() if len(df) > 1 else 5.0,
            'std_rebounds': df['rebounds'].std() if len(df) > 1 else 2.0,
            'std_assists': df['assists'].std() if len(df) > 1 else 2.0
        }

        return result

    def get_comprehensive_team_stats(self, team_name):
        """
        Get all comprehensive team statistics
        Returns dict with all relevant team stats
        """
        self.connect_db()

        query = """
            SELECT defensive_rating, offensive_rating, pace, net_rating,
                   opp_points_pg, opp_fg_pct, opp_three_pct,
                   points_pg, field_goal_pct, three_point_pct,
                   efg_pct, fta_rate, tm_tov_pct, true_shooting_pct
            FROM team_stats
            WHERE team_name = ?
            ORDER BY date DESC
            LIMIT 1
        """

        df = pd.read_sql_query(query, self.conn, params=(team_name,))

        if df.empty:
            # Return league averages
            return {
                'defensive_rating': 112.0,
                'offensive_rating': 112.0,
                'pace': 100.0,
                'net_rating': 0.0,
                'opp_points_pg': 112.0,
                'opp_fg_pct': 0.465,
                'opp_three_pct': 0.365,
                'points_pg': 112.0,
                'field_goal_pct': 0.465,
                'three_point_pct': 0.365,
                'efg_pct': 0.540,
                'fta_rate': 0.220,
                'tm_tov_pct': 0.140,
                'true_shooting_pct': 0.580
            }

        row = df.iloc[0]
        return {
            'defensive_rating': row['defensive_rating'] if pd.notna(row['defensive_rating']) else 112.0,
            'offensive_rating': row['offensive_rating'] if pd.notna(row['offensive_rating']) else 112.0,
            'pace': row['pace'] if pd.notna(row['pace']) else 100.0,
            'net_rating': row['net_rating'] if pd.notna(row['net_rating']) else 0.0,
            'opp_points_pg': row['opp_points_pg'] if pd.notna(row['opp_points_pg']) else 112.0,
            'opp_fg_pct': row['opp_fg_pct'] if pd.notna(row['opp_fg_pct']) else 0.465,
            'opp_three_pct': row['opp_three_pct'] if pd.notna(row['opp_three_pct']) else 0.365,
            'points_pg': row['points_pg'] if pd.notna(row['points_pg']) else 112.0,
            'field_goal_pct': row['field_goal_pct'] if pd.notna(row['field_goal_pct']) else 0.465,
            'three_point_pct': row['three_point_pct'] if pd.notna(row['three_point_pct']) else 0.365,
            'efg_pct': row['efg_pct'] if pd.notna(row['efg_pct']) else 0.540,
            'fta_rate': row['fta_rate'] if pd.notna(row['fta_rate']) else 0.220,
            'tm_tov_pct': row['tm_tov_pct'] if pd.notna(row['tm_tov_pct']) else 0.140,
            'true_shooting_pct': row['true_shooting_pct'] if pd.notna(row['true_shooting_pct']) else 0.580
        }

    def calculate_defensive_matchup_impact(self, opponent_team, position='G'):
        """
        Calculate how opponent's defense affects scoring
        Uses comprehensive defensive stats
        Returns a multiplier (< 1 for tough defense, > 1 for weak defense)
        """
        team_stats = self.get_comprehensive_team_stats(opponent_team)

        # League averages
        league_avg_def = 112.0
        league_avg_pace = 100.0
        league_avg_opp_fg = 0.465

        # 1. Defensive Rating Impact (40% weight)
        def_rating = team_stats['defensive_rating']
        def_rating_impact = league_avg_def / def_rating if def_rating > 0 else 1.0

        # 2. Pace Impact (30% weight)
        pace = team_stats['pace']
        pace_impact = pace / league_avg_pace if pace > 0 else 1.0

        # 3. Opponent FG% Allowed (30% weight) - actual defensive performance
        opp_fg_pct = team_stats['opp_fg_pct']
        # Higher opponent FG% = weaker defense = easier to score
        fg_defense_impact = opp_fg_pct / league_avg_opp_fg if opp_fg_pct > 0 else 1.0

        # Combined impact with weights
        combined_impact = (def_rating_impact * 0.40) + (pace_impact * 0.30) + (fg_defense_impact * 0.30)

        return combined_impact

    def calculate_offensive_environment_impact(self, opponent_team):
        """
        Calculate scoring environment based on opponent's offensive rating
        High-scoring teams = more possessions and faster games
        """
        team_stats = self.get_comprehensive_team_stats(opponent_team)

        league_avg_off = 112.0
        opp_off_rating = team_stats['offensive_rating']

        # Teams with high offensive ratings push the pace and create more opportunities
        # Slight positive correlation with opponent scoring
        off_env_impact = 1.0 + ((opp_off_rating - league_avg_off) / league_avg_off) * 0.15

        # Cap between 0.95 and 1.05
        return max(0.95, min(1.05, off_env_impact))

    def calculate_shooting_efficiency_factor(self, opponent_team):
        """
        Factor based on opponent's defensive shooting metrics
        Better 3PT defense = harder for players to score efficiently
        """
        team_stats = self.get_comprehensive_team_stats(opponent_team)

        league_avg_three_def = 0.365
        opp_three_pct = team_stats['opp_three_pct']

        # Higher 3PT% allowed = weaker 3PT defense = boost for shooters
        three_defense_factor = opp_three_pct / league_avg_three_def if opp_three_pct > 0 else 1.0

        # Cap between 0.92 and 1.08
        return max(0.92, min(1.08, three_defense_factor))

    def analyze_opponent_injuries(self, opponent_team):
        """
        Analyze opponent's injury situation and its impact on defense
        Key defenders out = easier scoring
        """
        self.connect_db()

        query = """
            SELECT player_name, injury_type, status
            FROM injury_report
            WHERE team = ? AND status IN ('Out', 'Doubtful')
            AND report_date >= date('now', '-7 days')
        """

        df = pd.read_sql_query(query, self.conn, params=(opponent_team,))

        if df.empty:
            return 1.0  # No injury impact

        # Each key player out increases scoring opportunity by 3-5%
        injury_boost = 1.0 + (len(df) * 0.04)

        # Cap at 15% boost
        return min(injury_boost, 1.15)

    def calculate_probability_distribution(self, player_name, opponent_team,
                                           is_home=True, player_injury=None, custom_factors=None):
        """
        Calculate probability distribution for player's scoring
        Returns predicted value and probability ranges

        custom_factors: dict with optional factor weights:
            - defensiveImpact: multiplier for defensive impact (default 1.0)
            - injuryBoost: multiplier for opponent injury boost (default 1.0)
            - homeAwayFactor: multiplier for home/away effect (default 1.0)
            - playerInjuryFactor: multiplier for player injury impact (default 1.0)
            - trendFactor: multiplier for trend analysis (default 1.0)
        """
        # Set default factors
        factors = {
            'defensiveImpact': 1.0,
            'injuryBoost': 1.0,
            'homeAwayFactor': 1.0,
            'playerInjuryFactor': 1.0,
            'trendFactor': 1.0,
            'offensiveEnvironment': 1.0,  # New: Opponent offensive rating impact
            'shootingEfficiency': 1.0     # New: Opponent 3PT defense impact
        }

        # Override with custom factors if provided
        if custom_factors:
            factors.update(custom_factors)
        # Get historical matchup data
        matchup_history = self.get_player_vs_team_history(player_name, opponent_team)
        season_avg = self.get_player_season_average(player_name)

        # Calculate base predictions
        if isinstance(matchup_history, pd.DataFrame) and not matchup_history.empty:
            # Use matchup-specific data
            base_points = matchup_history['points'].mean()
            base_rebounds = matchup_history['rebounds'].mean()
            base_assists = matchup_history['assists'].mean()
            base_steals = matchup_history['steals'].mean()
            base_blocks = matchup_history['blocks'].mean()
            base_turnovers = matchup_history['turnovers'].mean()

            # Calculate standard deviations
            std_points = matchup_history['points'].std() if len(matchup_history) > 1 else 5.0
            std_rebounds = matchup_history['rebounds'].std() if len(matchup_history) > 1 else 2.0
            std_assists = matchup_history['assists'].std() if len(matchup_history) > 1 else 2.0

            # Calculate trend (recent vs older games)
            if len(matchup_history) >= 3:
                recent_avg = matchup_history.head(3)['points'].mean()
                older_avg = matchup_history.tail(3)['points'].mean()
                trend_factor = recent_avg / older_avg if older_avg > 0 else 1.0
            else:
                trend_factor = 1.0
        else:
            # Use season averages
            base_points = season_avg.get('avg_points', 15.0)
            base_rebounds = season_avg.get('avg_rebounds', 5.0)
            base_assists = season_avg.get('avg_assists', 4.0)
            base_steals = season_avg.get('avg_steals', 1.0)
            base_blocks = season_avg.get('avg_blocks', 0.5)
            base_turnovers = season_avg.get('avg_turnovers', 2.0)

            std_points = season_avg.get('std_points', 5.0)
            std_rebounds = season_avg.get('std_rebounds', 2.0)
            std_assists = season_avg.get('std_assists', 2.0)

            trend_factor = 1.0

        # Apply adjustments

        # 1. Defensive matchup impact (with custom weight)
        base_def_impact = self.calculate_defensive_matchup_impact(opponent_team)
        def_impact = 1.0 + (base_def_impact - 1.0) * factors['defensiveImpact']

        # 2. Opponent injury impact (with custom weight)
        base_injury_impact = self.analyze_opponent_injuries(opponent_team)
        injury_impact = 1.0 + (base_injury_impact - 1.0) * factors['injuryBoost']

        # 3. Home/Away factor (with custom weight)
        base_home_factor = 1.05 if is_home else 0.95
        home_factor = 1.0 + (base_home_factor - 1.0) * factors['homeAwayFactor']

        # 4. Player injury impact (with custom weight)
        base_player_injury_factor = 1.0
        if player_injury and player_injury != 'healthy':
            injury_impacts = {
                'ankle': 0.80,
                'knee': 0.70,
                'back': 0.75,
                'hamstring': 0.75,
                'questionable': 0.90,
                'probable': 0.95
            }
            base_player_injury_factor = injury_impacts.get(player_injury.lower(), 0.85)

        player_injury_factor = 1.0 + (base_player_injury_factor - 1.0) * factors['playerInjuryFactor']

        # 5. Apply trend factor weight
        weighted_trend_factor = 1.0 + (trend_factor - 1.0) * factors['trendFactor']

        # 6. NEW: Offensive Environment Impact (opponent's offensive rating)
        base_off_env = self.calculate_offensive_environment_impact(opponent_team)
        off_env_impact = 1.0 + (base_off_env - 1.0) * factors['offensiveEnvironment']

        # 7. NEW: Shooting Efficiency Factor (opponent's 3PT defense)
        base_shoot_eff = self.calculate_shooting_efficiency_factor(opponent_team)
        shoot_eff_impact = 1.0 + (base_shoot_eff - 1.0) * factors['shootingEfficiency']

        # Store factor breakdown for display
        factor_breakdown = {
            'defensiveImpact': {
                'value': round(def_impact, 3),
                'base': round(base_def_impact, 3),
                'weight': factors['defensiveImpact']
            },
            'injuryBoost': {
                'value': round(injury_impact, 3),
                'base': round(base_injury_impact, 3),
                'weight': factors['injuryBoost']
            },
            'homeAwayFactor': {
                'value': round(home_factor, 3),
                'base': round(base_home_factor, 3),
                'weight': factors['homeAwayFactor']
            },
            'playerInjuryFactor': {
                'value': round(player_injury_factor, 3),
                'base': round(base_player_injury_factor, 3),
                'weight': factors['playerInjuryFactor']
            },
            'trendFactor': {
                'value': round(weighted_trend_factor, 3),
                'base': round(trend_factor, 3),
                'weight': factors['trendFactor']
            },
            'offensiveEnvironment': {
                'value': round(off_env_impact, 3),
                'base': round(base_off_env, 3),
                'weight': factors['offensiveEnvironment']
            },
            'shootingEfficiency': {
                'value': round(shoot_eff_impact, 3),
                'base': round(base_shoot_eff, 3),
                'weight': factors['shootingEfficiency']
            }
        }

        # Calculate final predictions with all factors
        final_points = base_points * def_impact * injury_impact * home_factor * player_injury_factor * weighted_trend_factor * off_env_impact * shoot_eff_impact
        final_rebounds = base_rebounds * home_factor * player_injury_factor
        final_assists = base_assists * home_factor * player_injury_factor
        final_steals = base_steals * player_injury_factor
        final_blocks = base_blocks * player_injury_factor
        final_turnovers = base_turnovers

        # Calculate confidence based on data quality
        if isinstance(matchup_history, pd.DataFrame) and len(matchup_history) >= 5:
            confidence = 0.85  # High confidence with good matchup data
        elif isinstance(matchup_history, pd.DataFrame) and len(matchup_history) >= 2:
            confidence = 0.70  # Medium confidence
        else:
            confidence = 0.60  # Lower confidence without matchup data

        # Adjust confidence based on factors
        if player_injury and player_injury != 'healthy':
            confidence *= 0.85

        # Calculate probability ranges (using normal distribution)
        predictions = {
            'points': {
                'prediction': round(final_points, 1),
                'lower_bound': round(max(0, final_points - 1.5 * std_points), 1),
                'upper_bound': round(final_points + 1.5 * std_points, 1),
                'confidence': round(confidence, 2),
                'probability_over_15': self.calculate_probability_over(final_points, std_points, 15),
                'probability_over_20': self.calculate_probability_over(final_points, std_points, 20),
                'probability_over_25': self.calculate_probability_over(final_points, std_points, 25),
                'probability_over_30': self.calculate_probability_over(final_points, std_points, 30)
            },
            'rebounds': {
                'prediction': round(final_rebounds, 1),
                'lower_bound': round(max(0, final_rebounds - 1.5 * std_rebounds), 1),
                'upper_bound': round(final_rebounds + 1.5 * std_rebounds, 1),
                'confidence': round(confidence, 2)
            },
            'assists': {
                'prediction': round(final_assists, 1),
                'lower_bound': round(max(0, final_assists - 1.5 * std_assists), 1),
                'upper_bound': round(final_assists + 1.5 * std_assists, 1),
                'confidence': round(confidence, 2)
            },
            'steals': {
                'prediction': round(final_steals, 1),
                'lower_bound': round(max(0, final_steals - 0.5), 1),
                'upper_bound': round(final_steals + 0.8, 1),
                'confidence': round(confidence * 0.9, 2)
            },
            'blocks': {
                'prediction': round(final_blocks, 1),
                'lower_bound': round(max(0, final_blocks - 0.3), 1),
                'upper_bound': round(final_blocks + 0.6, 1),
                'confidence': round(confidence * 0.85, 2)
            },
            'turnovers': {
                'prediction': round(final_turnovers, 1),
                'lower_bound': round(max(0, final_turnovers - 1.0), 1),
                'upper_bound': round(final_turnovers + 1.5, 1),
                'confidence': round(confidence * 0.8, 2)
            },
            'minutes': {
                'prediction': round(season_avg.get('avg_minutes', 30.0) * player_injury_factor, 1),
                'lower_bound': round(season_avg.get('avg_minutes', 30.0) * player_injury_factor - 5, 1),
                'upper_bound': round(season_avg.get('avg_minutes', 30.0) * player_injury_factor + 3, 1),
                'confidence': round(confidence, 2)
            }
        }

        # Generate analysis
        analysis = self.generate_detailed_analysis(
            player_name, opponent_team, matchup_history,
            def_impact, injury_impact, home_factor, player_injury_factor,
            confidence
        )

        predictions['analysis'] = analysis
        predictions['factors'] = {
            'defensive_impact': round(def_impact, 3),
            'opponent_injuries_boost': round(injury_impact, 3),
            'home_advantage': round(home_factor, 3),
            'player_injury_impact': round(player_injury_factor, 3),
            'trend_factor': round(weighted_trend_factor, 3),
            'offensive_environment': round(off_env_impact, 3),  # NEW
            'shooting_efficiency': round(shoot_eff_impact, 3),  # NEW
            'games_vs_opponent': len(matchup_history) if isinstance(matchup_history, pd.DataFrame) else 0
        }
        predictions['factor_breakdown'] = factor_breakdown
        predictions['base_average'] = round(base_points, 1)

        # Add team stats context
        team_stats = self.get_comprehensive_team_stats(opponent_team)
        predictions['team_stats'] = {
            'defensive_rating': round(team_stats['defensive_rating'], 1),
            'offensive_rating': round(team_stats['offensive_rating'], 1),
            'pace': round(team_stats['pace'], 1),
            'net_rating': round(team_stats['net_rating'], 1),
            'opp_fg_pct': round(team_stats['opp_fg_pct'], 3),
            'opp_three_pct': round(team_stats['opp_three_pct'], 3)
        }

        return predictions

    def calculate_probability_over(self, mean, std, threshold):
        """Calculate probability of scoring over a threshold"""
        if std == 0:
            std = 0.1
        z_score = (threshold - mean) / std
        probability = 1 - stats.norm.cdf(z_score)
        return round(probability * 100, 1)

    def generate_detailed_analysis(self, player_name, opponent, matchup_history,
                                    def_impact, injury_impact, home_factor,
                                    player_injury_factor, confidence):
        """Generate comprehensive analysis text"""
        analysis = []

        # Matchup history analysis
        if isinstance(matchup_history, pd.DataFrame) and not matchup_history.empty:
            games_count = len(matchup_history)
            avg_vs_team = matchup_history['points'].mean()
            analysis.append(f"📊 {games_count} game(s) vs {opponent}: averaging {avg_vs_team:.1f} PPG")

            if games_count >= 3:
                recent_3 = matchup_history.head(3)['points'].mean()
                analysis.append(f"📈 Last 3 games vs {opponent}: {recent_3:.1f} PPG")
        else:
            analysis.append(f"ℹ️ Limited matchup history vs {opponent} - using season averages")

        # Defensive matchup
        if def_impact < 0.95:
            analysis.append(f"🛡️ Tough defensive matchup ({((1-def_impact)*100):.1f}% harder to score)")
        elif def_impact > 1.05:
            analysis.append(f"✅ Favorable defensive matchup (+{((def_impact-1)*100):.1f}% easier to score)")

        # Opponent injuries
        if injury_impact > 1.05:
            analysis.append(f"🏥 Opponent dealing with injuries (+{((injury_impact-1)*100):.1f}% scoring boost)")

        # Home/Away
        if home_factor > 1.0:
            analysis.append(f"🏠 Home court advantage (+5% expected boost)")
        else:
            analysis.append(f"✈️ Away game (-5% expected impact)")

        # Player injury
        if player_injury_factor < 1.0:
            analysis.append(f"⚠️ Player injury concern ({((1-player_injury_factor)*100):.1f}% performance decrease)")

        # Confidence
        if confidence >= 0.80:
            analysis.append(f"💪 High confidence prediction ({confidence:.0%})")
        elif confidence >= 0.65:
            analysis.append(f"📊 Moderate confidence ({confidence:.0%})")
        else:
            analysis.append(f"⚠️ Lower confidence ({confidence:.0%}) - limited data")

        return "\n".join(analysis)

    def predict_performance(self, player_name, opponent, game_date,
                           is_home=True, injury_status=None, custom_factors=None):
        """
        Main prediction function with probability calculations
        custom_factors: Optional dict with factor weights (defensiveImpact, injuryBoost, etc.)
        """
        try:
            predictions = self.calculate_probability_distribution(
                player_name, opponent, is_home, injury_status, custom_factors
            )
            return predictions
        finally:
            self.close_db()

    def compare_players(self, player1, player2, opponent, game_date):
        """Compare two players with probability-based predictions"""
        try:
            pred1 = self.calculate_probability_distribution(player1, opponent, True, None)
            pred2 = self.calculate_probability_distribution(player2, opponent, True, None)

            # Calculate fantasy points
            fp1 = self.calculate_fantasy_points(pred1)
            fp2 = self.calculate_fantasy_points(pred2)

            # Generate recommendation
            if fp1 > fp2 * 1.1:
                recommendation = f"Strong recommendation: {player1} (projected {fp1:.1f} FP vs {fp2:.1f} FP, {((fp1/fp2-1)*100):.1f}% advantage)"
            elif fp2 > fp1 * 1.1:
                recommendation = f"Strong recommendation: {player2} (projected {fp2:.1f} FP vs {fp1:.1f} FP, {((fp2/fp1-1)*100):.1f}% advantage)"
            else:
                recommendation = f"Close matchup: {player1} ({fp1:.1f} FP) vs {player2} ({fp2:.1f} FP) - {abs(fp1-fp2):.1f} FP difference"

            return {
                'player1': {'name': player1, 'predictions': pred1, 'fantasy_points': fp1},
                'player2': {'name': player2, 'predictions': pred2, 'fantasy_points': fp2},
                'recommendation': recommendation
            }
        finally:
            self.close_db()

    def calculate_fantasy_points(self, predictions):
        """Calculate fantasy points from predictions"""
        scoring = {
            'points': 1.0,
            'rebounds': 1.2,
            'assists': 1.5,
            'steals': 3.0,
            'blocks': 3.0,
            'turnovers': -1.0
        }

        total = 0
        for stat, multiplier in scoring.items():
            if stat in predictions:
                total += predictions[stat]['prediction'] * multiplier

        return total

# Example usage
if __name__ == "__main__":
    predictor = AdvancedNBAPredictor()

    # Test prediction
    result = predictor.predict_performance(
        player_name="LeBron James",
        opponent="BOS",
        game_date=datetime(2024, 12, 15),
        is_home=True,
        injury_status=None
    )

    print("Advanced Prediction Results:")
    print("=" * 60)
    for stat, values in result.items():
        if stat not in ['analysis', 'factors']:
            print(f"\n{stat.upper()}:")
            print(f"  Prediction: {values['prediction']}")
            print(f"  Range: {values['lower_bound']} - {values['upper_bound']}")
            print(f"  Confidence: {values['confidence']:.0%}")
            if 'probability_over_20' in values:
                print(f"  Probability >20: {values['probability_over_20']:.1f}%")

    print(f"\nAnalysis:\n{result['analysis']}")
    print(f"\nFactors:\n{result['factors']}")
