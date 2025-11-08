# StatMuse Integration Guide

## Overview

StatMuse integration adds **granular "little stats"** to the NBA Player Predictor, enhancing predictions with detailed matchup-specific data that goes beyond standard NBA API statistics.

## What StatMuse Provides

StatMuse offers detailed, situational NBA statistics that improve prediction accuracy:

### 1. **Matchup-Specific Performance**
- Player stats vs specific opponents (last 5, 10, 15 games)
- Historical averages against each team
- Game-by-game performance breakdowns

**Example:** "LeBron James averaged 32.8 PPG vs Warriors in last 5 games"

### 2. **Recent Form Analysis**
- Last 5/10 game averages
- Performance trends
- Hot/cold streak detection

**Example:** "Stephen Curry: 31.2 PPG in last 5 games"

### 3. **Home/Away Splits**
- Performance at home vs on the road
- Location impact quantification
- Home court advantage analysis

**Example:** "Giannis: 28.5 PPG at home, 25.1 PPG away"

### 4. **Clutch Performance**
- 4th quarter statistics
- Late-game scoring ability
- Pressure situation performance

**Example:** "Kevin Durant: 8.2 PPG in 4th quarter"

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Elite NBA Predictor                        │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │
│  │   NBA API   │  │  StatMuse   │  │ Other Sources    │    │
│  │  (Official) │  │  (Granular) │  │ (Basketball Ref) │    │
│  └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘    │
│         │                │                   │               │
│         └────────────────┴───────────────────┘               │
│                          │                                   │
│                   ┌──────▼──────┐                           │
│                   │  Prediction  │                           │
│                   │    Engine    │                           │
│                   └──────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Scraping** (scheduled/on-demand)
   ```
   StatMuse Website → StatMuse Scraper → SQLite Database
   ```

2. **Prediction** (live)
   ```
   Prediction Request → Check DB Cache → Retrieve StatMuse Data → Apply Factors → Enhanced Prediction
   ```

### Cache Strategy

- **Database Storage**: Scraped data cached in SQLite
- **24-Hour TTL**: Data refreshed daily
- **Memory Cache**: In-memory cache for active sessions
- **Rate Limiting**: 2-second delay between requests (respectful scraping)

## File Structure

```
backend/
├── statmuse_scraper.py          # Core scraper implementation
├── elite_predictor.py            # Enhanced with StatMuse integration
├── nba_data_fetcher.py           # Updated with StatMuse as data source
├── populate_statmuse_data.py    # Helper script for pre-population
└── database/
    └── nba_data.db               # SQLite with statmuse_data table
```

## Usage

### Pre-populate Data (Recommended)

Run this before using predictions to avoid slow live scraping:

```bash
cd backend

# Populate recent form for top 30 players (quick)
python populate_statmuse_data.py --mode form --players 30

# Populate key matchups (slower, more comprehensive)
python populate_statmuse_data.py --mode matchups --players 20

# Full population (form + matchups)
python populate_statmuse_data.py --mode full --players 30
```

### Manual Scraping

```python
from statmuse_scraper import StatMuseScraper

scraper = StatMuseScraper()

# Fetch comprehensive stats for a player
stats = scraper.fetch_comprehensive_player_stats(
    player_name='LeBron James',
    opponent_team='Golden State Warriors'
)

# Individual queries
recent_form = scraper.fetch_recent_form('Stephen Curry', last_n_games=5)
home_away = scraper.fetch_home_away_splits('Giannis Antetokounmpo')
clutch = scraper.fetch_clutch_stats('Kevin Durant')
```

### Predictions with StatMuse

StatMuse factors are automatically integrated when you use the elite predictor:

```python
from elite_predictor import EliteNBAPredictor

predictor = EliteNBAPredictor()

result = predictor.elite_predict_performance(
    player_name="LeBron James",
    opponent="Golden State Warriors",
    game_date=datetime(2025, 11, 15),
    is_home=True,
    player_position='F',
    player_team='Los Angeles Lakers'
)

# StatMuse factors included in result
print(result['elite_factors']['statmuse_impact'])
print(result['elite_analysis'])  # Includes StatMuse insights
```

## Impact on Predictions

### Adjustment Factors

StatMuse data applies multiplicative adjustments to predictions:

| Factor | Impact | Example |
|--------|--------|---------|
| **Matchup History** | ±20% | Player averaging 30% more vs opponent |
| **Recent Form** | ±15% | Hot streak = +15% boost |
| **Home/Away Split** | ±10% | Strong home performance = +10% |
| **Clutch Factor** | ±5% | 4th quarter specialist = +5% |

### Confidence Boost

StatMuse data increases prediction confidence:
- **+10 points**: Matchup history available (3+ games)
- **+5 points**: Recent form data available
- **+5 points**: Home/away splits available

## Database Schema

```sql
CREATE TABLE statmuse_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT,           -- e.g., "LeBron James"
    data_type TEXT,             -- 'vs_opponent', 'recent_form_5', 'home_away_splits', 'clutch_stats'
    opponent TEXT,              -- e.g., "Golden State Warriors" (empty for non-matchup types)
    data_json TEXT,             -- Full JSON data
    fetched_at TIMESTAMP,       -- When data was scraped
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Rate Limiting & Ethics

### Respectful Scraping

- **2-second delay** between requests
- **User-Agent** identification
- **Caching** to minimize requests
- **Scheduled updates** instead of real-time scraping

### Best Practices

1. ✅ **Pre-populate data** using the helper script
2. ✅ **Run updates daily** or weekly, not per prediction
3. ✅ **Cache aggressively** (24-hour TTL)
4. ❌ **Don't scrape** during every prediction
5. ❌ **Don't hammer** the StatMuse servers

## Troubleshooting

### No StatMuse Data in Predictions

**Cause**: Data not populated in database

**Solution**:
```bash
python populate_statmuse_data.py --mode form --players 50
```

### Scraping Errors

**Cause**: Rate limiting, network issues, or HTML structure changes

**Solution**:
1. Check internet connection
2. Verify StatMuse website is accessible
3. Check if HTML structure changed (update scraper if needed)

### Missing Matchup Data

**Cause**: Specific player-opponent combo not scraped

**Solution**:
```python
from statmuse_scraper import StatMuseScraper
scraper = StatMuseScraper()
scraper.fetch_comprehensive_player_stats('Player Name', 'Opponent Team')
```

## API Endpoints Enhanced

StatMuse integration enhances these API endpoints:

### `/api/predict` (POST)

**Enhanced Output**:
```json
{
  "points": {...},
  "elite_factors": {
    "statmuse_impact": {
      "impact_factor": 1.15,
      "confidence_boost": 15,
      "data_available": true
    }
  },
  "elite_analysis": "📊 StatMuse: Averaged 28.5 PPG vs Warriors (10 games)\n🔥 Strong matchup history (+15% boost)\n..."
}
```

## Performance

### Speed

- **With Cache**: <50ms (DB lookup)
- **Without Cache**: ~5-10s (live scraping)
- **Recommended**: Pre-populate data

### Storage

- **Per Player**: ~5-10 KB (all stat types)
- **50 Players**: ~250-500 KB
- **Minimal Impact**: On SQLite database

## Future Enhancements

Potential additions:
- [ ] Rest days impact from StatMuse
- [ ] Month-by-month trends
- [ ] Playoff vs regular season splits
- [ ] Time of season performance (early vs late)
- [ ] Back-to-back game performance
- [ ] Against specific defenders

## Summary

StatMuse integration adds the "little stats" that make predictions more accurate by:

1. **Matchup Specificity**: Historical performance vs today's opponent
2. **Current Form**: Recent game trends
3. **Situational Context**: Home/away, clutch, etc.
4. **Confidence**: More data = better predictions

**Result**: More accurate, contextual, and confident NBA player performance predictions!
