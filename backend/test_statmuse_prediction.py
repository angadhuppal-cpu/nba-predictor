#!/usr/bin/env python3
"""
Test StatMuse Integration with Elite Predictor
Demonstrates how granular statistics enhance predictions
"""

from elite_predictor import EliteNBAPredictor
from datetime import datetime
import json

def test_prediction_with_statmuse():
    """
    Run a test prediction to showcase StatMuse integration
    """
    print("="*70)
    print("NBA ELITE PREDICTOR - StatMuse Integration Test")
    print("="*70)

    # Initialize predictor
    print("\nInitializing Elite Predictor with StatMuse integration...")
    predictor = EliteNBAPredictor()
    print("[OK] Predictor initialized!")

    # Test prediction for a popular player
    print("\n" + "="*70)
    print("TEST PREDICTION: LeBron James vs Golden State Warriors")
    print("="*70)

    try:
        result = predictor.elite_predict_performance(
            player_name="LeBron James",
            opponent="Golden State Warriors",
            game_date=datetime(2025, 11, 15),
            is_home=True,
            injury_status=None,
            player_position='F',
            player_team='Los Angeles Lakers'
        )

        print("\nPREDICTION RESULTS")
        print("-" * 70)

        # Display main predictions
        print(f"\nPoints:    {result['points']['prediction']} "
              f"(Range: {result['points']['lower_bound']} - {result['points']['upper_bound']})")
        print(f"Rebounds:  {result['rebounds']['prediction']}")
        print(f"Assists:   {result['assists']['prediction']}")
        print(f"Minutes:   {result['minutes']['prediction']}")

        # Display confidence
        print(f"\nConfidence: {result.get('confidence', 'N/A')}%")

        # Display elite factors
        print("\n" + "="*70)
        print("ELITE FACTORS")
        print("="*70)

        elite_factors = result.get('elite_factors', {})

        print(f"\nUsage Rate: {elite_factors.get('usage_rate', 'N/A')}%")
        print(f"True Shooting: {elite_factors.get('true_shooting_pct', 'N/A')}%")
        print(f"Pace Impact: {elite_factors.get('pace_impact', 'N/A')}")

        # Teammate injuries
        teammate_impact = elite_factors.get('teammate_injury_impact', {})
        print(f"\nTeammate Injuries: {teammate_impact.get('context', 'N/A')}")
        if teammate_impact.get('injured_count', 0) > 0:
            print(f"   Usage Boost: {teammate_impact.get('usage_boost', 1.0)}")
            print(f"   Minutes Boost: {teammate_impact.get('minutes_boost', 1.0)}")

        # Defender matchup
        defender = elite_factors.get('defender_matchup', {})
        print(f"\nMatchup Difficulty: {defender.get('difficulty', 'N/A')}")
        print(f"   Impact Factor: {defender.get('impact', 'N/A')}")
        if defender.get('historical', '') != 'No historical data':
            print(f"   {defender.get('historical', '')}")

        # StatMuse impact (THE KEY PART!)
        print("\n" + "="*70)
        print("STATMUSE GRANULAR STATISTICS")
        print("="*70)

        statmuse = elite_factors.get('statmuse_impact', {})
        if statmuse.get('data_available', False):
            print(f"\n[OK] StatMuse Data: AVAILABLE")
            print(f"   Impact Factor: {statmuse.get('impact_factor', 1.0)}")
            print(f"   Confidence Boost: +{statmuse.get('confidence_boost', 0)} points")
        else:
            print(f"\n[!] StatMuse Data: NOT CACHED")
            print(f"   [i] Run 'populate_statmuse_data.py' to cache granular stats")
            print(f"   Impact Factor: {statmuse.get('impact_factor', 1.0)} (neutral - no adjustment)")

        # Display full analysis
        print("\n" + "="*70)
        print("DETAILED ANALYSIS")
        print("="*70)
        print()
        print(result.get('elite_analysis', 'No analysis available'))

        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"\nPrediction for LeBron James vs Warriors:")
        print(f"  • {result['points']['prediction']} points")
        print(f"  • {result['rebounds']['prediction']} rebounds")
        print(f"  • {result['assists']['prediction']} assists")
        print(f"\nFactors considered:")
        print(f"  • Usage rate, shooting efficiency, pace")
        print(f"  • Teammate injuries, defender matchup")
        print(f"  • StatMuse granular stats: {'[OK] Applied' if statmuse.get('data_available') else '[X] Not cached'}")

    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*70)
    print("[OK] TEST COMPLETE!")
    print("="*70)

    return True

def show_statmuse_instructions():
    """Show instructions for populating StatMuse data"""
    print("\n" + "="*70)
    print("HOW TO POPULATE STATMUSE DATA")
    print("="*70)
    print()
    print("To see StatMuse granular stats in predictions, run:")
    print()
    print("  # Quick (recent form for top 30 players - ~5 minutes)")
    print("  python populate_statmuse_data.py --mode form --players 30")
    print()
    print("  # Full (all stats for top 20 players - ~30 minutes)")
    print("  python populate_statmuse_data.py --mode full --players 20")
    print()
    print("This will cache:")
    print("  - Player vs opponent history")
    print("  - Recent form (last 5 games)")
    print("  - Home/away splits")
    print("  - Clutch performance (4th quarter)")
    print()
    print("="*70)

if __name__ == '__main__':
    success = test_prediction_with_statmuse()

    if success:
        show_statmuse_instructions()
        print("\n[TIP]: The prediction works even without StatMuse data cached!")
        print("       StatMuse adds extra accuracy when available.")
