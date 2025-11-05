#!/usr/bin/env python3
"""
Fetch comprehensive game logs for top NBA players
"""
import sqlite3
from nba_data_pipeline import NBADataPipeline
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_comprehensive_game_logs():
    """Fetch game logs for top 100 players from last 2 seasons"""

    pipeline = NBADataPipeline()
    pipeline.connect_db()

    # Get top 100 players by scoring average
    cursor = pipeline.conn.cursor()
    cursor.execute("""
        SELECT player_id, player_name, team, points_avg
        FROM player_season_stats
        WHERE games_played >= 10
        ORDER BY points_avg DESC
        LIMIT 100
    """)

    top_players = cursor.fetchall()
    logger.info(f"Fetching game logs for {len(top_players)} top players...")

    seasons = ['2024-25', '2023-24']  # Current and last season
    total_games = 0

    for idx, (player_id, player_name, team, ppg) in enumerate(top_players, 1):
        logger.info(f"[{idx}/100] {player_name} ({team}) - {ppg:.1f} PPG")

        player_games = []

        for season in seasons:
            try:
                # Fetch game logs
                game_logs = pipeline.fetch_player_game_logs(str(player_id), season)

                if not game_logs.empty:
                    logger.info(f"  ✓ Found {len(game_logs)} games in {season}")
                    player_games.append(game_logs)

            except Exception as e:
                logger.error(f"  ✗ Error fetching {season}: {e}")
                continue

        # Save all games for this player
        if player_games:
            all_games = pd.concat(player_games, ignore_index=True)
            save_game_logs_to_db(pipeline.conn, all_games, player_name, team)
            total_games += len(all_games)
            logger.info(f"  ✓ Saved {len(all_games)} total games")

    pipeline.close_db()

    logger.info(f"\n✅ Complete! Fetched {total_games} games for {len(top_players)} players")

def save_game_logs_to_db(conn, df, player_name, team):
    """Save game logs to database"""
    cursor = conn.cursor()

    for _, row in df.iterrows():
        try:
            # Parse opponent from MATCHUP column (e.g., "MIL vs. PHX" or "MIL @ LAL")
            matchup = row.get('MATCHUP', '')

            if ' vs. ' in matchup:
                opponent_abbrev = matchup.split(' vs. ')[1]
            elif ' @ ' in matchup:
                opponent_abbrev = matchup.split(' @ ')[1]
            else:
                continue

            # Convert abbreviation to full name
            opponent = abbrev_to_full_name(opponent_abbrev)

            cursor.execute("""
                INSERT OR REPLACE INTO player_stats (
                    player_id, player_name, team, date, opponent,
                    points, rebounds, assists, steals, blocks, turnovers,
                    field_goals_made, field_goals_attempted,
                    three_pointers_made, three_pointers_attempted,
                    free_throws_made, free_throws_attempted,
                    minutes, plus_minus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get('Player_ID', ''),
                player_name,
                team,
                row.get('GAME_DATE', ''),
                opponent,
                row.get('PTS', 0),
                row.get('REB', 0),
                row.get('AST', 0),
                row.get('STL', 0),
                row.get('BLK', 0),
                row.get('TOV', 0),
                row.get('FGM', 0),
                row.get('FGA', 0),
                row.get('FG3M', 0),
                row.get('FG3A', 0),
                row.get('FTM', 0),
                row.get('FTA', 0),
                row.get('MIN', 0),
                row.get('PLUS_MINUS', 0)
            ))
        except Exception as e:
            logger.error(f"Error saving game: {e}")
            continue

    conn.commit()

def abbrev_to_full_name(abbrev):
    """Convert team abbreviation to full name"""
    mapping = {
        'ATL': 'Atlanta Hawks',
        'BOS': 'Boston Celtics',
        'BKN': 'Brooklyn Nets',
        'CHA': 'Charlotte Hornets',
        'CHI': 'Chicago Bulls',
        'CLE': 'Cleveland Cavaliers',
        'DAL': 'Dallas Mavericks',
        'DEN': 'Denver Nuggets',
        'DET': 'Detroit Pistons',
        'GSW': 'Golden State Warriors',
        'HOU': 'Houston Rockets',
        'IND': 'Indiana Pacers',
        'LAC': 'LA Clippers',
        'LAL': 'Los Angeles Lakers',
        'MEM': 'Memphis Grizzlies',
        'MIA': 'Miami Heat',
        'MIL': 'Milwaukee Bucks',
        'MIN': 'Minnesota Timberwolves',
        'NOP': 'New Orleans Pelicans',
        'NYK': 'New York Knicks',
        'OKC': 'Oklahoma City Thunder',
        'ORL': 'Orlando Magic',
        'PHI': 'Philadelphia 76ers',
        'PHX': 'Phoenix Suns',
        'POR': 'Portland Trail Blazers',
        'SAC': 'Sacramento Kings',
        'SAS': 'San Antonio Spurs',
        'TOR': 'Toronto Raptors',
        'UTA': 'Utah Jazz',
        'WAS': 'Washington Wizards'
    }
    return mapping.get(abbrev, abbrev)

if __name__ == '__main__':
    fetch_comprehensive_game_logs()
