# NBA Data Pipeline Documentation

## Overview

The NBA Data Pipeline is a comprehensive system for fetching real NBA player statistics, team rosters, and game data from official NBA sources.

## Features

✅ **Real NBA Data Fetching**
- All active NBA players
- Complete team rosters (which team has which players)
- Season statistics for all players
- Game-by-game performance logs
- Team statistics (offensive/defensive ratings, pace)
- Injury reports
- Game schedules

✅ **Automated Updates**
- Daily full updates at 3 AM
- Quick updates every 6 hours
- Manual on-demand updates

✅ **Data Sources**
- Official NBA Stats API (stats.nba.com)
- Rate-limited to respect API guidelines
- Error handling and retry logic

## Installation

### Required Packages

```bash
pip install requests pandas numpy apscheduler
```

These are already included in `backend/requirements.txt`.

## Usage

### Option 1: Management CLI (Recommended)

The easiest way to use the pipeline is through the management CLI:

```bash
cd backend
source venv/bin/activate

# Show current database status
python manage_data.py status

# Fetch all NBA data (one-time full fetch)
python manage_data.py fetch

# Fetch only team rosters
python manage_data.py fetch-rosters

# Fetch only player statistics
python manage_data.py fetch-stats

# Search for a player
python manage_data.py search "LeBron James"

# List all teams
python manage_data.py teams

# Start automated scheduler
python manage_data.py schedule
```

### Option 2: Direct Python Import

```python
from nba_data_pipeline import NBADataPipeline

# Initialize pipeline
pipeline = NBADataPipeline()

# Fetch all data and save to database
pipeline.save_to_database()

# Or fetch specific data
players = pipeline.fetch_all_players()
rosters = pipeline.fetch_team_rosters()
season_stats = pipeline.fetch_player_season_stats()
team_stats = pipeline.fetch_team_stats()
```

### Option 3: Automated Scheduler

Start the automated scheduler to keep data fresh:

```bash
python data_scheduler.py
```

Or run a one-time update:

```bash
python data_scheduler.py now
```

## Data Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   NBA Data Pipeline                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   1. Fetch All Active Players         │
        │      (commonallplayers API)           │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   2. Fetch Team Rosters               │
        │      (commonteamroster API)           │
        │      • Player-Team mapping            │
        │      • Position, height, weight       │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   3. Fetch Player Season Stats        │
        │      (leaguedashplayerstats API)      │
        │      • PPG, RPG, APG, etc.            │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   4. Fetch Team Statistics            │
        │      (leaguedashteamstats API)        │
        │      • Offensive/Defensive ratings    │
        │      • Pace, Net Rating               │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   5. Fetch Game Logs (Top Players)    │
        │      (playergamelog API)              │
        │      • Historical game-by-game stats  │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   Save to SQLite Database             │
        │      • player_season_stats            │
        │      • player_stats                   │
        │      • team_stats                     │
        └───────────────────────────────────────┘
```

## API Endpoints Used

### 1. Common All Players
- **Endpoint**: `commonallplayers`
- **Purpose**: Get all active NBA players
- **Data**: Player ID, name, team, years active

### 2. Common Team Roster
- **Endpoint**: `commonteamroster`
- **Purpose**: Get team roster details
- **Data**: Player ID, name, number, position, height, weight

### 3. League Dash Player Stats
- **Endpoint**: `leaguedashplayerstats`
- **Purpose**: Season statistics for all players
- **Data**: Games played, minutes, points, rebounds, assists, shooting %

### 4. League Dash Team Stats
- **Endpoint**: `leaguedashteamstats`
- **Purpose**: Team-level statistics
- **Data**: Offensive rating, defensive rating, pace, net rating

### 5. Player Game Log
- **Endpoint**: `playergamelog`
- **Purpose**: Game-by-game player statistics
- **Data**: Date, opponent, points, rebounds, assists per game

## Database Schema

### player_season_stats
Stores season averages for each player:
- player_id, player_name, team
- games_played, minutes_avg
- points_avg, rebounds_avg, assists_avg
- field_goal_pct, three_point_pct, free_throw_pct

### player_stats
Stores individual game statistics:
- player_id, player_name, team, date, opponent
- points, rebounds, assists, steals, blocks, turnovers
- shooting stats, plus_minus

### team_stats
Stores team statistics:
- team_id, team_name, season
- offensive_rating, defensive_rating, pace
- wins, losses, net_rating

## Rate Limiting

The pipeline includes automatic rate limiting to respect NBA API guidelines:
- **Delay**: 600ms between requests
- **Timeout**: 30 seconds per request
- **Retry**: Automatic error handling

## Example Workflows

### Initial Setup (First Time)

```bash
# 1. Initialize database
cd database
python init_db.py

# 2. Fetch all NBA data
cd ../backend
source venv/bin/activate
python manage_data.py fetch

# 3. Check status
python manage_data.py status

# 4. Search for a player to verify
python manage_data.py search "LeBron"
```

### Daily Updates (Automated)

```bash
# Start the scheduler (runs in background)
python manage_data.py schedule

# Or add to systemd/cron for production
# Cron example (runs daily at 3 AM):
# 0 3 * * * cd /path/to/backend && python data_scheduler.py now
```

### Manual Update

```bash
# Quick manual update
python manage_data.py fetch-stats

# Or use the scheduler for one-time run
python data_scheduler.py now
```

## Estimated Data Volumes

Based on current NBA season:

- **Active Players**: ~450 players
- **Teams**: 30 teams
- **Season Stats Records**: ~450 records
- **Game Logs** (top 50 players, last 30 games): ~1,500 records
- **Team Stats**: 30 records

**Total Initial Database Size**: ~15-20 MB

## Performance

- **Full Pipeline Run**: 5-10 minutes
- **Roster Only**: 1-2 minutes
- **Stats Only**: 2-3 minutes
- **API Rate**: ~100 requests/minute

## Troubleshooting

### "Error fetching data"
- Check internet connection
- NBA Stats API may be temporarily down
- Try again in a few minutes

### "Rate limit exceeded"
- Pipeline already includes delays
- If still seeing errors, increase `request_delay` in `nba_data_pipeline.py`

### "No data returned"
- Check if it's NBA off-season
- Verify database path is correct
- Check logs in `../logs/data_pipeline.log`

### "Database locked"
- Close any other connections to the database
- Stop the Flask app temporarily if running
- Run pipeline again

## Production Deployment

### Using Systemd (Linux)

Create `/etc/systemd/system/nba-data-scheduler.service`:

```ini
[Unit]
Description=NBA Data Pipeline Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/python data_scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable nba-data-scheduler
sudo systemctl start nba-data-scheduler
```

### Using Cron

Add to crontab (`crontab -e`):

```bash
# Full update daily at 3 AM
0 3 * * * cd /path/to/backend && /path/to/venv/bin/python data_scheduler.py now >> /path/to/logs/cron.log 2>&1

# Quick update every 6 hours
0 */6 * * * cd /path/to/backend && /path/to/venv/bin/python -c "from data_scheduler import DataScheduler; DataScheduler().run_quick_update()"
```

## Data Freshness

- **Player Stats**: Updated daily
- **Team Stats**: Updated every 6 hours
- **Rosters**: Updated daily (changes are rare during season)
- **Game Logs**: Updated daily for recent games

## API Documentation

For detailed NBA Stats API documentation, see:
- https://github.com/swar/nba_api
- https://www.nba.com/stats/

## Support

For issues or questions:
1. Check logs in `../logs/data_pipeline.log`
2. Run `python manage_data.py status` to verify database
3. Check GitHub issues

## License

This data pipeline fetches publicly available NBA statistics.
Please respect NBA's terms of service and rate limits.

---

**Note**: The NBA Stats API is unofficial and may change without notice.
Always verify data accuracy with official NBA sources.
