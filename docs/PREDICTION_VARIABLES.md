# Prediction Variables Documentation

## Overview
The NBA Performance Prediction System evaluates **22 comprehensive variables** across 6 categories to generate accurate player performance predictions.

## Complete Variable List

### 1. Historical Base Data (3 variables)
| Variable | Description | Source |
|----------|-------------|--------|
| **Base Average Points** | Historical average points vs specific opponent or season average | Database: player_stats table |
| **Games vs Opponent** | Number of historical matchups used in analysis | Calculated from player_stats |
| **Standard Deviation** | Statistical variance in scoring performance | Calculated from historical points |

### 2. Defensive Matchup Analysis (6 variables)
| Variable | Description | Impact |
|----------|-------------|--------|
| **Opponent Defensive Rating** | Opponent's defensive efficiency (points allowed per 100 possessions) | Lower rating = tougher defense |
| **Opponent Pace** | Opponent's game pace (possessions per 48 minutes) | Faster pace = more opportunities |
| **League Average Defensive Rating** | Standard baseline (110.0) | Comparison reference |
| **League Average Pace** | Standard baseline (100.0) | Comparison reference |
| **Defensive Multiplier** | `league_avg_def / opponent_def_rating` | 0.85 - 1.15 range |
| **Pace Multiplier** | `opponent_pace / league_avg_pace` | 0.90 - 1.10 range |

### 3. Opponent Injury Impact (3 variables)
| Variable | Description | Formula |
|----------|-------------|---------|
| **Injured Players Count** | Number of opponent's key players out/doubtful | Query injury_report table |
| **Base Injury Boost** | Raw scoring boost from opponent injuries | `1.0 + (injured_count × 0.04)` |
| **Injury Boost Weight** | User-customizable multiplier | 0.0 - 2.0 (default: 1.0) |

### 4. Home/Away Analysis (2 variables)
| Variable | Description | Effect |
|----------|-------------|--------|
| **Base Home Factor** | Standard home court advantage | Home: 1.05 (+5%), Away: 0.95 (-5%) |
| **Home Factor Weight** | User-customizable multiplier | 0.5 - 1.5 (default: 1.0) |

### 5. Player Health Impact (3 variables)
| Variable | Description | Injury Type Impact |
|----------|-------------|-------------------|
| **Player Injury Type** | Specific injury classification | Ankle: 80%, Knee: 70%, Back: 75%, Hamstring: 75% |
| **Base Player Injury Factor** | Type-specific performance reduction | 0.70 - 1.0 range |
| **Player Injury Weight** | User-customizable multiplier | 0.0 - 1.5 (default: 1.0) |

### 6. Recent Form & Trends (3 variables)
| Variable | Description | Calculation |
|----------|-------------|-------------|
| **Recent Form Average** | Average points from last 3 games vs opponent | Query player_stats (limit 3) |
| **Older Form Average** | Average points from older 3 games vs opponent | Query player_stats (tail 3) |
| **Trend Factor** | Ratio of recent to older performance | `recent_avg / older_avg` |

### 7. Final Prediction Variables (2 variables)
| Variable | Description | Formula |
|----------|-------------|---------|
| **Final Points Prediction** | Adjusted prediction after all factors | `base_avg × def_impact × injury_boost × home_factor × player_injury × trend` |
| **Confidence Level** | Statistical confidence based on data quality | 60% (limited data) to 85% (5+ matchup games) |

## Calculation Flow

```
Step 1: Get Base Average
├── Query historical games vs opponent
└── Fallback to season average if < 2 games

Step 2: Calculate Defensive Impact
├── Defensive Multiplier = league_avg_def / opponent_def_rating
├── Pace Multiplier = opponent_pace / league_avg_pace
└── Combined Impact = (def_mult × 0.6) + (pace_mult × 0.4)

Step 3: Analyze Opponent Injuries
├── Count injured key players (Out/Doubtful)
├── Base Boost = 1.0 + (count × 0.04)
└── Cap at 1.15 (15% max boost)

Step 4: Apply Home/Away Factor
└── Home: 1.05 (+5%) | Away: 0.95 (-5%)

Step 5: Apply Player Injury Impact
├── Healthy: 1.0
├── Ankle: 0.80 (-20%)
├── Knee: 0.70 (-30%)
├── Back: 0.75 (-25%)
├── Hamstring: 0.75 (-25%)
├── Questionable: 0.90 (-10%)
└── Probable: 0.95 (-5%)

Step 6: Calculate Trend Factor
├── Recent (last 3 games) vs Older (tail 3 games)
└── Trend = recent_avg / older_avg

Step 7: Apply Custom Factor Weights
├── Each factor × user weight (0.5 - 2.0)
└── Final adjusted multipliers

Step 8: Calculate Final Prediction
└── Final = Base × Def × Injury × Home × Player Health × Trend
```

## Example Calculation

**Scenario:** Stephen Curry vs Phoenix Suns (Home Game, Healthy)

```
Input Variables:
- Base Average: 25.3 PPG (vs PHX historical)
- Games vs Opponent: 8 games
- Opponent Def Rating: 112.5
- Opponent Pace: 102.3
- Opponent Injuries: 2 key players out
- Is Home: Yes
- Player Injury: None
- Recent Form: 28.7 PPG (last 3)
- Older Form: 24.2 PPG (older 3)

Calculations:
1. Defensive Impact = (110.0/112.5 × 0.6) + (102.3/100.0 × 0.4)
   = (0.978 × 0.6) + (1.023 × 0.4) = 0.587 + 0.409 = 0.996

2. Injury Boost = 1.0 + (2 × 0.04) = 1.08 (+8%)

3. Home Factor = 1.05 (+5%)

4. Player Injury = 1.0 (healthy)

5. Trend Factor = 28.7 / 24.2 = 1.186 (+18.6%)

6. Final Prediction = 25.3 × 0.996 × 1.08 × 1.05 × 1.0 × 1.186
   = 25.3 × 1.338 = 33.8 points

Confidence: 85% (8 games vs opponent = high confidence)
```

## User Customization

Users can adjust 5 factor weights through the UI:

1. **Defensive Impact Weight** (0.5 - 1.5)
   - Higher = More emphasis on opponent defense strength

2. **Injury Boost Weight** (0.0 - 2.0)
   - Higher = More boost from opponent injuries

3. **Home/Away Weight** (0.5 - 1.5)
   - Higher = Stronger home court advantage effect

4. **Player Injury Weight** (0.0 - 1.5)
   - Higher = More severe impact from player injuries

5. **Trend Weight** (0.5 - 1.5)
   - Higher = More weight on recent vs historical form

## Data Sources

All variables are calculated from the following database tables:

- **player_stats**: Individual game logs (12,505 games)
- **player_season_stats**: Season averages (540 players)
- **team_stats**: Team defensive ratings and pace (30 teams)
- **injury_report**: Current injury status (updated daily)

## Statistical Methods

- **Normal Distribution**: Used for probability calculations (over/under thresholds)
- **Standard Deviation**: Determines prediction ranges and confidence intervals
- **Z-Score**: Calculates probability of exceeding specific point totals
- **Confidence Intervals**: ±1.5 standard deviations (68% probability range)

## API Response Structure

```json
{
  "base_average": 25.3,
  "factors": {
    "defensive_impact": 0.996,
    "opponent_injuries_boost": 1.08,
    "home_advantage": 1.05,
    "player_injury_impact": 1.0,
    "trend_factor": 1.186,
    "games_vs_opponent": 8
  },
  "factor_breakdown": {
    "defensiveImpact": {
      "value": 0.996,
      "base": 0.996,
      "weight": 1.0
    },
    // ... (other factors)
  },
  "points": {
    "prediction": 33.8,
    "lower_bound": 26.3,
    "upper_bound": 41.3,
    "confidence": 0.85,
    "probability_over_15": 98.2,
    "probability_over_20": 94.1,
    "probability_over_25": 78.3,
    "probability_over_30": 52.7
  }
}
```

## Version History

- **v1.0** (Initial): Basic prediction with season averages
- **v2.0** (Advanced): Added defensive matchups, injuries, home/away
- **v3.0** (Current): Added custom factor weights and trend analysis

---

**Last Updated:** November 4, 2025
**Total Variables:** 22
**Algorithm:** Multi-factor weighted probability distribution
