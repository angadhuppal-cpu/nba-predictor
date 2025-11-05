# Team Statistics Pipeline - Quick Start Guide

## What It Does
Fetches comprehensive offensive and defensive statistics for all 30 NBA teams from the official NBA Stats API.

## Quick Start

### 1. Fetch Team Stats (One-Time)
```bash
cd backend
source venv/bin/activate
python fetch_team_stats.py
```

This will:
- Update database schema (if needed)
- Fetch stats from NBA API for all 30 teams
- Save to `team_stats` table
- Display summary of all teams

### 2. Run Automated Updates (Optional)
```bash
python team_stats_scheduler.py
```

This will:
- Run updates every 6 hours
- Run daily comprehensive update at 4:00 AM
- Keep running in background

## API Endpoints

### Get All Teams
```bash
GET http://localhost:5000/api/team-stats
```

Response:
```json
{
  "teams": [
    {
      "team": "Oklahoma City Thunder",
      "off": 119.2,
      "def": 106.6,
      "net": 12.7,
      "pace": 100.9,
      "record": "8-2"
    },
    ...
  ]
}
```

### Get Specific Team
```bash
GET http://localhost:5000/api/team-stats?team=Boston%20Celtics
```

Response:
```json
{
  "team": "Boston Celtics",
  "record": {"wins": 9, "losses": 2},
  "ratings": {
    "offensive": 119.5,
    "defensive": 110.1,
    "net": 9.4,
    "pace": 96.6
  },
  "offense": {
    "ppg": 120.1,
    "fg_pct": 0.476,
    "three_pct": 0.390,
    "ft_pct": 0.791,
    "apg": 25.4,
    "rpg": 48.2,
    "tov_pg": 13.6
  },
  "defense": {
    "opp_ppg": 109.5,
    "opp_fg_pct": 0.451,
    "opp_three_pct": 0.357
  },
  ...
}
```

## What Stats Are Fetched

### Key Metrics
- **Offensive Rating**: Points per 100 possessions (league avg: ~112)
- **Defensive Rating**: Points allowed per 100 possessions (lower is better)
- **Net Rating**: Offensive - Defensive Rating
- **Pace**: Possessions per 48 minutes (league avg: ~100)

### Traditional Stats
- Points, FG%, 3P%, FT%
- Assists, Rebounds, Turnovers

### Advanced Metrics
- True Shooting %, Effective FG%
- Opponent stats (defensive impact)
- Four Factors (eFG%, TOV%, FTA Rate, OREB%)

## Database Schema

```sql
-- View current schema
sqlite3 ../database/nba_data.db "PRAGMA table_info(team_stats);"

-- Query example
sqlite3 ../database/nba_data.db "SELECT team_name, offensive_rating, defensive_rating FROM team_stats ORDER BY net_rating DESC LIMIT 10;"
```

## Files

- `fetch_team_stats.py` - Main pipeline script
- `team_stats_scheduler.py` - Automated scheduler
- `nba_data_pipeline.py` - Base NBA API client
- `docs/TEAM_STATS_PIPELINE.md` - Full documentation

## Current Data (2024-25 Season)

**Top Offensive Teams:**
1. Cleveland Cavaliers (121.0)
2. Boston Celtics (119.5)
3. Oklahoma City Thunder (119.2)

**Top Defensive Teams:**
1. Oklahoma City Thunder (106.6)
2. LA Clippers (109.4)
3. Orlando Magic (109.1)

**Fastest Pace:**
1. Memphis Grizzlies (103.7)
2. Chicago Bulls (103.6)
3. Atlanta Hawks (103.4)

## Troubleshooting

**Error: Module not found**
```bash
pip install requests pandas numpy
```

**Error: Database locked**
```bash
# Stop Flask server first
pkill -f "python app.py"
# Then run fetch script
python fetch_team_stats.py
```

**Error: API rate limit**
- Wait 1-2 minutes and retry
- Script has built-in 600ms delay between requests

## Usage in Predictions

Team stats are automatically used in predictions:
- Defensive Rating → affects player point projections
- Pace → affects possession opportunities
- Opponent stats → defensive matchup analysis

See `backend/advanced_predictor.py:112-149` for implementation.

---

For complete documentation, see `docs/TEAM_STATS_PIPELINE.md`
