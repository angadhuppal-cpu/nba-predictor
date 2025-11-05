"""
NBA Player Performance Prediction System
A comprehensive analytics tool for predicting player performance based on multiple factors
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
warnings.filterwarnings('ignore')

class NBAPredictor:
    """
    Advanced NBA player performance prediction system that considers:
    - Historical performance patterns
    - Injury impact and recovery time
    - Fatigue from back-to-back games
    - Home vs away performance
    - Matchup history against specific teams
    - Rest days between games
    - Season progression effects
    """

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.player_data = pd.DataFrame()
        self.team_data = pd.DataFrame()
        self.injury_data = pd.DataFrame()
        self.schedule_data = pd.DataFrame()

    def fetch_player_stats(self, season='2023-24'):
        """Fetch comprehensive player statistics from NBA API"""
        # Note: In production, you'd use official NBA API or reliable data source
        # This is a structure for the data collection
        print(f"Fetching player stats for season {season}...")

        # Simulated data structure - replace with actual API calls
        base_url = "https://stats.nba.com/stats"

        # Player stats endpoint structure
        endpoints = {
            'player_stats': '/leaguedashplayerstats',
            'player_bio': '/commonallplayers',
            'team_stats': '/leaguedashteamstats',
            'injuries': '/injuries',
            'schedule': '/leaguegamelog'
        }

        # Headers required for NBA stats API
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://stats.nba.com',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        }

        return self.player_data

    def calculate_fatigue_factor(self, player_id, game_date):
        """
        Calculate fatigue based on:
        - Back-to-back games
        - Games in last 5 days
        - Minutes played recently
        - Travel distance
        """
        fatigue_score = 0.0

        # Check for back-to-back games
        previous_day = game_date - timedelta(days=1)
        if self.check_game_played(player_id, previous_day):
            fatigue_score += 0.15  # 15% performance decrease for back-to-back

        # Check games in last 5 days
        games_last_5 = self.count_recent_games(player_id, game_date, days=5)
        if games_last_5 >= 3:
            fatigue_score += 0.10  # Additional 10% for 3+ games in 5 days

        # Check minutes played in last 3 games
        avg_minutes = self.get_recent_minutes(player_id, games=3)
        if avg_minutes > 35:
            fatigue_score += 0.08  # Heavy minutes burden

        return min(fatigue_score, 0.30)  # Cap at 30% fatigue impact

    def analyze_injury_impact(self, player_id, injury_type=None):
        """
        Analyze how injuries affect performance:
        - Type of injury
        - Days since return
        - Historical recovery patterns
        """
        if not injury_type:
            return 0.0

        injury_impacts = {
            'ankle': {'initial_impact': 0.20, 'recovery_days': 14},
            'knee': {'initial_impact': 0.30, 'recovery_days': 21},
            'back': {'initial_impact': 0.25, 'recovery_days': 14},
            'hamstring': {'initial_impact': 0.25, 'recovery_days': 18},
            'shoulder': {'initial_impact': 0.15, 'recovery_days': 10},
            'concussion': {'initial_impact': 0.35, 'recovery_days': 14},
            'finger': {'initial_impact': 0.10, 'recovery_days': 7},
            'quad': {'initial_impact': 0.20, 'recovery_days': 14}
        }

        if injury_type.lower() in injury_impacts:
            impact_data = injury_impacts[injury_type.lower()]
            return impact_data['initial_impact']

        return 0.15  # Default impact for unknown injuries

    def calculate_matchup_advantage(self, player_id, opponent_team):
        """
        Calculate player's historical performance against specific team:
        - Average stats vs this opponent
        - Win/loss record
        - Home vs away considerations
        """
        # Get historical data against opponent
        historical_games = self.get_games_vs_team(player_id, opponent_team)

        if historical_games.empty:
            return 1.0  # Neutral if no history

        # Calculate performance ratio
        season_avg = self.get_season_average(player_id)
        vs_team_avg = historical_games.mean()

        performance_ratio = vs_team_avg / season_avg if season_avg > 0 else 1.0

        return performance_ratio

    def build_prediction_model(self, target='points'):
        """
        Build ensemble model for predicting specific stats
        Uses Random Forest + Gradient Boosting for robust predictions
        """
        print(f"Building prediction model for {target}...")

        # Feature engineering
        features = [
            'games_played', 'minutes_avg', 'usage_rate', 'pace_factor',
            'days_rest', 'is_home', 'opponent_def_rating', 'recent_form',
            'fatigue_factor', 'injury_impact', 'matchup_history',
            'season_progression', 'team_record', 'opponent_record',
            'altitude_factor', 'travel_distance', 'time_zone_change'
        ]

        # Prepare training data
        X = self.player_data[features]
        y = self.player_data[target]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Build ensemble model
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42
        )

        gb_model = GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=10,
            random_state=42
        )

        # Train models
        rf_model.fit(X_train_scaled, y_train)
        gb_model.fit(X_train_scaled, y_train)

        # Ensemble predictions (weighted average)
        rf_weight = 0.6
        gb_weight = 0.4

        # Store models
        self.models[f'{target}_rf'] = rf_model
        self.models[f'{target}_gb'] = gb_model
        self.scalers[target] = scaler

        return self.models

    def predict_performance(self, player_name, opponent, game_date,
                           is_home=True, injury_status=None):
        """
        Main prediction function that combines all factors
        Returns predicted stats with confidence intervals
        """
        predictions = {}

        # Get player ID and basic info
        player_id = self.get_player_id(player_name)

        # Calculate all factors
        fatigue = self.calculate_fatigue_factor(player_id, game_date)
        injury_impact = self.analyze_injury_impact(player_id, injury_status)
        matchup_adv = self.calculate_matchup_advantage(player_id, opponent)

        # Get opponent defensive ratings
        opp_def_rating = self.get_team_defensive_rating(opponent)

        # Prepare features for prediction
        features = self.prepare_prediction_features(
            player_id, opponent, game_date, is_home,
            fatigue, injury_impact, matchup_adv, opp_def_rating
        )

        # Predict each stat category
        stat_categories = ['points', 'rebounds', 'assists', 'steals',
                          'blocks', 'turnovers', 'minutes']

        for stat in stat_categories:
            if f'{stat}_rf' in self.models:
                # Get predictions from both models
                rf_pred = self.models[f'{stat}_rf'].predict(features)[0]
                gb_pred = self.models[f'{stat}_gb'].predict(features)[0]

                # Weighted ensemble
                final_pred = (0.6 * rf_pred + 0.4 * gb_pred)

                # Apply adjustments
                final_pred *= (1 - fatigue)  # Reduce for fatigue
                final_pred *= (1 - injury_impact)  # Reduce for injury
                final_pred *= matchup_adv  # Adjust for matchup

                # Calculate confidence interval
                std_dev = self.calculate_prediction_std(stat, player_id)

                predictions[stat] = {
                    'prediction': round(final_pred, 1),
                    'lower_bound': round(final_pred - std_dev, 1),
                    'upper_bound': round(final_pred + std_dev, 1),
                    'confidence': self.calculate_confidence_score(
                        fatigue, injury_impact, matchup_adv
                    )
                }

        # Add additional insights
        predictions['analysis'] = self.generate_analysis(
            player_name, opponent, fatigue, injury_impact, matchup_adv
        )

        return predictions

    def calculate_confidence_score(self, fatigue, injury, matchup):
        """Calculate confidence in prediction based on factors"""
        base_confidence = 0.75

        # Reduce confidence for high fatigue
        if fatigue > 0.20:
            base_confidence -= 0.10

        # Reduce confidence for injuries
        if injury > 0:
            base_confidence -= (injury * 0.3)

        # Adjust for matchup history
        if matchup < 0.8 or matchup > 1.2:
            base_confidence -= 0.05

        return max(min(base_confidence, 0.95), 0.40)

    def generate_analysis(self, player, opponent, fatigue, injury, matchup):
        """Generate detailed analysis text for the prediction"""
        analysis = []

        # Fatigue analysis
        if fatigue > 0.15:
            analysis.append(f"⚠️ High fatigue factor ({fatigue:.1%}) due to recent schedule")
        elif fatigue > 0.05:
            analysis.append(f"📊 Moderate fatigue ({fatigue:.1%}) from recent games")

        # Injury analysis
        if injury > 0:
            analysis.append(f"🏥 Injury impact reducing expected performance by {injury:.1%}")

        # Matchup analysis
        if matchup > 1.15:
            analysis.append(f"✅ Historically performs well vs {opponent} (+{(matchup-1):.1%})")
        elif matchup < 0.85:
            analysis.append(f"⚠️ Historically struggles vs {opponent} ({(1-matchup):.1%})")

        # Additional factors
        analysis.append(f"📈 Model confidence: {self.calculate_confidence_score(fatigue, injury, matchup):.1%}")

        return "\n".join(analysis)

    def get_player_comparison(self, player1, player2, opponent, game_date):
        """Compare two players' predicted performance"""
        pred1 = self.predict_performance(player1, opponent, game_date)
        pred2 = self.predict_performance(player2, opponent, game_date)

        comparison = {
            'player1': {'name': player1, 'predictions': pred1},
            'player2': {'name': player2, 'predictions': pred2},
            'recommendation': self.generate_recommendation(pred1, pred2, player1, player2)
        }

        return comparison

    def generate_recommendation(self, pred1, pred2, name1, name2):
        """Generate recommendation based on predictions"""
        # Calculate fantasy points projection
        fp1 = self.calculate_fantasy_points(pred1)
        fp2 = self.calculate_fantasy_points(pred2)

        if fp1 > fp2 * 1.1:
            return f"Strong recommendation: {name1} (projected {fp1:.1f} FP vs {fp2:.1f} FP)"
        elif fp2 > fp1 * 1.1:
            return f"Strong recommendation: {name2} (projected {fp2:.1f} FP vs {fp1:.1f} FP)"
        else:
            return f"Close matchup: {name1} ({fp1:.1f} FP) vs {name2} ({fp2:.1f} FP)"

    def calculate_fantasy_points(self, predictions):
        """Calculate DFS fantasy points from predictions"""
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

    # Helper methods (stubs - would connect to real data)
    def check_game_played(self, player_id, date):
        """Check if player played on specific date"""
        return False  # Placeholder

    def count_recent_games(self, player_id, date, days):
        """Count games played in recent days"""
        return 2  # Placeholder

    def get_recent_minutes(self, player_id, games):
        """Get average minutes in recent games"""
        return 32.5  # Placeholder

    def get_games_vs_team(self, player_id, team):
        """Get historical games against team"""
        return pd.DataFrame()  # Placeholder

    def get_season_average(self, player_id):
        """Get season averages for player"""
        return 20.5  # Placeholder

    def get_player_id(self, player_name):
        """Get player ID from name"""
        return "123"  # Placeholder

    def get_team_defensive_rating(self, team):
        """Get team's defensive rating"""
        return 110.5  # Placeholder

    def prepare_prediction_features(self, player_id, opponent, date,
                                   is_home, fatigue, injury, matchup, def_rating):
        """Prepare feature vector for prediction"""
        # This would compile all features into proper format
        return np.array([[25, 32.5, 0.25, 100, 2, 1, 110.5, 0.8,
                         fatigue, injury, matchup, 0.4, 0.65, 0.55,
                         0, 0, 0]]).reshape(1, -1)

    def calculate_prediction_std(self, stat, player_id):
        """Calculate standard deviation for predictions"""
        return 3.5  # Placeholder

# Example usage
if __name__ == "__main__":
    # Initialize predictor
    predictor = NBAPredictor()

    # Example prediction
    print("NBA Player Performance Predictor")
    print("=" * 50)

    # Predict for a specific game
    prediction = predictor.predict_performance(
        player_name="LeBron James",
        opponent="Boston Celtics",
        game_date=datetime(2024, 12, 15),
        is_home=True,
        injury_status=None
    )

    print(f"\nPrediction for LeBron James vs Boston Celtics:")
    print("-" * 40)
    for stat, values in prediction.items():
        if stat != 'analysis':
            print(f"{stat.capitalize():10} {values['prediction']:6.1f} "
                  f"({values['lower_bound']:.1f} - {values['upper_bound']:.1f}) "
                  f"Confidence: {values['confidence']:.1%}")

    print(f"\nAnalysis:\n{prediction['analysis']}")
