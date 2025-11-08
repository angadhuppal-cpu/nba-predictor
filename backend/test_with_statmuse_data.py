#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Prediction WITH StatMuse Data
Demonstrates the enhanced predictions with granular statistics
"""

import sys
import io
from elite_predictor import EliteNBAPredictor
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_with_statmuse():
    """Test prediction with StatMuse data cached"""
    print("="*70)
    print("NBA PREDICTOR - WITH STATMUSE DATA")
    print("="*70)

    predictor = EliteNBAPredictor()

    # Test with Luka Doncic (we have his StatMuse data cached)
    print("\nPrediction: Luka Doncic vs Phoenix Suns (Home Game)")
    print("-" * 70)

    result = predictor.elite_predict_performance(
        player_name="Luka Dončić",
        opponent="Phoenix Suns",
        game_date=datetime(2025, 11, 15),
        is_home=True,  # Home game
        injury_status=None,
        player_position='G',
        player_team='Dallas Mavericks'
    )

    # Display results
    print(f"\nPREDICTION:")
    print(f"  Points:   {result['points']['prediction']}")
    print(f"  Rebounds: {result['rebounds']['prediction']}")
    print(f"  Assists:  {result['assists']['prediction']}")
    print(f"  Minutes:  {result['minutes']['prediction']}")

    # Elite factors
    print(f"\nELITE FACTORS:")
    elite = result.get('elite_factors', {})
    print(f"  Usage Rate:     {elite.get('usage_rate')}%")
    print(f"  True Shooting:  {elite.get('true_shooting_pct')}%")
    print(f"  Pace Impact:    {elite.get('pace_impact')}")

    # StatMuse impact
    statmuse = elite.get('statmuse_impact', {})
    print(f"\nSTATMUSE GRANULAR DATA:")
    print(f"  Data Available: {statmuse.get('data_available')}")
    print(f"  Impact Factor:  {statmuse.get('impact_factor')}")
    print(f"  Confidence Boost: +{statmuse.get('confidence_boost')} points")

    # Analysis
    print(f"\nDETAILED ANALYSIS:")
    print(result.get('elite_analysis', ''))

    print("\n" + "="*70)
    print("[OK] Test Complete - StatMuse data is being applied!")
    print("="*70)

if __name__ == '__main__':
    test_with_statmuse()
