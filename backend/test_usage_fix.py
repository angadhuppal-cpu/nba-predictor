#!/usr/bin/env python3
"""Test that usage rates are now correctly fetched from database"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from elite_predictor import EliteNBAPredictor
from datetime import datetime

predictor = EliteNBAPredictor()

print("="*70)
print("TESTING USAGE RATE FIX - DATABASE CACHE")
print("="*70)

# Test with Luka Dončić
test_players = [
    ('Luka Dončić', 'Dallas Mavericks'),
    ('Giannis Antetokounmpo', 'Milwaukee Bucks'),
    ('Stephen Curry', 'Golden State Warriors'),
    ('LeBron James', 'Los Angeles Lakers'),
    ('Tyrese Maxey', 'Philadelphia 76ers')
]

print("\nTesting players (should all show correct usage rates from database):\n")

for player_name, team in test_players:
    usage_data = predictor.get_usage_rate(player_name)
    if usage_data:
        ts = usage_data.get('true_shooting', 0)
        ts_display = ts * 100 if ts else 0
        print(f"{player_name:<30} Usage: {usage_data['rate']:>5.1f}%  TS: {ts_display:>5.1f}%  Source: {usage_data['source']}")
    else:
        print(f"{player_name:<30} - No data found!")

print("\n" + "="*70)

# Test a full prediction for Luka
print("FULL PREDICTION TEST - LUKA DONČIĆ")
print("="*70)

prediction = predictor.elite_predict_performance(
    player_name='Luka Dončić',
    opponent='Phoenix Suns',
    game_date=datetime(2025, 11, 8),
    is_home=True,
    player_team='Dallas Mavericks',
    player_position='G'
)

print(f"\nPredicted Points: {prediction['points']['prediction']}")
print(f"\nElite Factors:")
print(f"  Usage Rate: {prediction['elite_factors']['usage_rate']}%")
print(f"  Source: {prediction['elite_factors']['usage_source']}")
print(f"  True Shooting: {prediction['elite_factors']['true_shooting_pct']}%")

print("\n" + "="*70)
print("[OK] If Luka shows 38.7% usage rate, the fix is working!")
print("="*70)
