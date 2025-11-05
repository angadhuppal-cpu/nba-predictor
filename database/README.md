# Database Directory

This directory contains the SQLite database and related scripts for the NBA Prediction System.

## Database Schema

### Tables

#### 1. player_stats
Stores individual game statistics for players.
- **Columns**: player_id, player_name, team, date, opponent, points, rebounds, assists, etc.
- **Indexes**: player_id, date, opponent

#### 2. team_stats
Stores team-level statistics and ratings.
- **Columns**: team_id, team_name, offensive_rating, defensive_rating, pace, etc.
- **Indexes**: team_id, date

#### 3. injury_report
Tracks player injuries and their status.
- **Columns**: player_id, injury_type, status, return_date, games_missed, etc.
- **Indexes**: player_id, status, report_date

#### 4. game_schedule
NBA game schedule and results.
- **Columns**: game_id, date, home_team, away_team, scores, status, etc.
- **Indexes**: date, home_team, away_team, game_id

#### 5. player_season_stats
Aggregated seasonal statistics for players.
- **Columns**: player_id, season, games_played, averages for all stats, etc.

#### 6. predictions_log
Logs predictions for accuracy tracking.
- **Columns**: player_id, game_date, predicted values, actual values, confidence, etc.

## Initialization

To initialize the database, run:

```bash
cd database
python init_db.py
```

This will create all necessary tables and indexes.

## Database File

- **Filename**: `nba_data.db`
- **Type**: SQLite 3
- **Location**: This directory

## Backup

Regular backups are recommended. To backup:

```bash
cp nba_data.db nba_data_backup_$(date +%Y%m%d).db
```

## Maintenance

### Clear old data
```sql
DELETE FROM player_stats WHERE date < date('now', '-2 years');
VACUUM;
```

### Verify integrity
```bash
sqlite3 nba_data.db "PRAGMA integrity_check;"
```

## Notes

- The database uses SQLite for simplicity and portability
- For production use with high traffic, consider PostgreSQL or MySQL
- Regular VACUUM operations keep the database optimized
