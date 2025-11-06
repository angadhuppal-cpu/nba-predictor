# NBA Data Database

## Current Database Status

**Last Updated:** November 6, 2025
**Season:** 2024-25 NBA Season

## Database Contents

- **Players:** 575 active NBA players with current season stats
- **Game Records:** 2,440 individual game logs
- **Teams:** 30 NBA teams with advanced statistics

## Data Sources

This database was populated using the NBA Stats API via `nba_data_pipeline.py`.

### Top Statistical Leaders (as of last update):
1. Shai Gilgeous-Alexander (OKC) - 32.7 PPG
2. Giannis Antetokounmpo (MIL) - 30.4 PPG
3. Nikola Jokić (DEN) - 29.6 PPG
4. Luka Dončić (DAL) - 28.2 PPG
5. Anthony Edwards (MIN) - 27.6 PPG

## Database Schema

### Tables:
- `player_season_stats` - Season averages for all players
- `player_stats` - Game-by-game statistics
- `team_stats` - Team statistics and ratings
- `injury_report` - Current injury status
- `game_schedule` - Upcoming games
- `predictions_log` - Historical predictions for accuracy tracking

## Updating the Database

To refresh with the latest NBA data, run:
```bash
cd backend
python nba_data_pipeline.py
```

**Note:** The pipeline respects NBA API rate limits (600ms between requests).

## Backup

A backup file `nba_data.db.backup` is maintained for recovery purposes.

## Database File

- **Location:** `database/nba_data.db`
- **Size:** ~648 KB
- **Format:** SQLite 3
