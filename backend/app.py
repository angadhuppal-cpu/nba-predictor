"""
Flask API Backend for NBA Prediction System
RESTful API for predictions and analytics
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import os
import sqlite3
from nba_predictor import NBAPredictor
from advanced_predictor import AdvancedNBAPredictor
from nba_data_fetcher import NBADataFetcher, AdvancedAnalytics

app = Flask(__name__, static_folder='../frontend/build')
CORS(app)

# Initialize prediction system
predictor = AdvancedNBAPredictor()  # Using advanced predictor with probability calculations
basic_predictor = NBAPredictor()  # Keep for fallback
data_fetcher = NBADataFetcher()
analytics = AdvancedAnalytics()

# Cache for frequently accessed data
cache = {
    'players': [],
    'teams': [],
    'last_update': None
}

# Team name to abbreviation mapping
TEAM_NAME_TO_ABBR = {
    'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
    'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
    'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
}

def get_team_abbr(team_name):
    """Convert full team name to abbreviation"""
    # If already an abbreviation, return as-is
    if team_name in ['ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET',
                     'GSW', 'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN',
                     'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SAS',
                     'TOR', 'UTA', 'WAS']:
        return team_name
    return TEAM_NAME_TO_ABBR.get(team_name, team_name)

def update_cache():
    """Update cached data from database"""
    global cache
    cache['last_update'] = datetime.now()

    try:
        # Fetch players from database
        conn = sqlite3.connect('../database/nba_data.db')
        cursor = conn.cursor()

        # Get all players with their season stats (minimum 5 games played for relevance)
        cursor.execute("""
            SELECT DISTINCT player_id, player_name, team, games_played, points_avg
            FROM player_season_stats
            WHERE games_played >= 5
            ORDER BY points_avg DESC
        """)

        players_data = cursor.fetchall()
        cache['players'] = [
            {
                'id': str(row[0]),
                'name': row[1],
                'team': row[2],
                'games': row[3],
                'ppg': round(row[4], 1)
            }
            for row in players_data
        ]

        # Get all teams
        cursor.execute("""
            SELECT DISTINCT team_name
            FROM team_stats
            ORDER BY team_name
        """)

        teams_data = cursor.fetchall()
        cache['teams'] = [row[0] for row in teams_data]

        conn.close()

        print(f"Cache updated: {len(cache['players'])} players, {len(cache['teams'])} teams")

    except Exception as e:
        print(f"Error updating cache: {e}")
        # Fallback to hardcoded data if database fails
        cache['players'] = [
            {'id': '2544', 'name': 'LeBron James', 'team': 'LAL', 'games': 70, 'ppg': 24.4},
            {'id': '1627750', 'name': 'Jayson Tatum', 'team': 'BOS', 'games': 74, 'ppg': 26.9},
            {'id': '203999', 'name': 'Nikola Jokic', 'team': 'DEN', 'games': 79, 'ppg': 26.4},
        ]
        cache['teams'] = [
            'LAL', 'BOS', 'MIL', 'PHX', 'DEN', 'GSW', 'MIA', 'PHI',
            'BKN', 'LAC', 'DAL', 'MEM', 'NOP', 'SAC', 'POR', 'NYK',
            'MIN', 'IND', 'ATL', 'CHI', 'CLE', 'DET', 'HOU', 'OKC',
            'ORL', 'SAS', 'TOR', 'UTA', 'WAS', 'CHA'
        ]

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve the React application"""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# API Routes
@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/players')
def get_players():
    """Get list of available players"""
    if not cache['players'] or not cache['last_update']:
        update_cache()
    return jsonify({'players': cache['players']})

@app.route('/api/teams')
def get_teams():
    """Get list of NBA teams"""
    if not cache['teams']:
        update_cache()
    return jsonify({'teams': cache['teams']})

@app.route('/api/history', methods=['GET'])
def get_player_history():
    """Get historical performance of a player vs opponent"""
    try:
        player_name = request.args.get('player')
        opponent_team = request.args.get('opponent')

        if not player_name or not opponent_team:
            return jsonify({'error': 'Missing player or opponent parameter'}), 400

        # Convert full team name to abbreviation
        opponent_abbr = get_team_abbr(opponent_team)

        # Fetch historical games from database
        conn = sqlite3.connect('../database/nba_data.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT date, opponent, points, rebounds, assists, steals, blocks,
                   field_goals_made, field_goals_attempted, three_pointers_made,
                   three_pointers_attempted, free_throws_made, free_throws_attempted,
                   turnovers, plus_minus
            FROM player_stats
            WHERE player_name = ? AND opponent = ?
            ORDER BY date DESC
            LIMIT 20
        """, (player_name, opponent_abbr))

        games = cursor.fetchall()
        conn.close()

        if not games:
            return jsonify({
                'player': player_name,
                'opponent': opponent_team,
                'games': [],
                'averages': None,
                'message': 'No historical data found for this matchup'
            })

        # Format game data
        game_history = []
        for game in games:
            game_history.append({
                'date': game[0],
                'opponent': game[1],
                'points': game[2],
                'rebounds': game[3],
                'assists': game[4],
                'steals': game[5],
                'blocks': game[6],
                'fg_made': game[7],
                'fg_attempted': game[8],
                'three_made': game[9],
                'three_attempted': game[10],
                'ft_made': game[11],
                'ft_attempted': game[12],
                'turnovers': game[13],
                'plus_minus': game[14]
            })

        # Calculate averages
        total_games = len(games)
        avg_points = sum(g[2] for g in games) / total_games
        avg_rebounds = sum(g[3] for g in games) / total_games
        avg_assists = sum(g[4] for g in games) / total_games

        return jsonify({
            'player': player_name,
            'opponent': opponent_team,
            'games': game_history,
            'total_games': total_games,
            'averages': {
                'points': round(avg_points, 1),
                'rebounds': round(avg_rebounds, 1),
                'assists': round(avg_assists, 1)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """Generate prediction for a player"""
    try:
        data = request.json

        # Validate required fields
        required_fields = ['player', 'opponent', 'game_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Convert injury status
        injury = None if data.get('injury_status') == 'healthy' else data.get('injury_status')

        # Get custom factors if provided
        custom_factors = data.get('custom_factors', None)

        # Get prediction
        prediction = predictor.predict_performance(
            player_name=data['player'],
            opponent=data['opponent'],
            game_date=datetime.strptime(data['game_date'], '%Y-%m-%d'),
            is_home=data.get('is_home', True),
            injury_status=injury,
            custom_factors=custom_factors
        )

        return jsonify(prediction)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def compare_players():
    """Compare two players' predicted performance"""
    try:
        data = request.json

        # Validate required fields
        required_fields = ['player1', 'player2', 'opponent', 'game_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        comparison = predictor.get_player_comparison(
            player1=data['player1'],
            player2=data['player2'],
            opponent=data['opponent'],
            game_date=datetime.strptime(data['game_date'], '%Y-%m-%d')
        )

        return jsonify(comparison)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-data', methods=['POST'])
def update_data():
    """Manually trigger data update"""
    try:
        data_fetcher.update_all_data()
        update_cache()
        return jsonify({'status': 'success', 'message': 'Data updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/schedule/<date>')
def get_schedule(date):
    """Get games scheduled for a specific date"""
    try:
        games = data_fetcher.fetch_schedule(date)
        return jsonify({'games': games.to_dict('records')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/injuries')
def get_injuries():
    """Get current injury report"""
    try:
        injuries = data_fetcher.fetch_injury_report()
        return jsonify({'injuries': injuries.to_dict('records')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player/<player_id>/recent')
def get_player_recent(player_id):
    """Get player's recent performance"""
    try:
        games = request.args.get('games', 10, type=int)
        recent = data_fetcher.get_recent_form(player_id, games=games)
        return jsonify(recent)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player/<player_id>/matchup/<team>')
def get_matchup_history(player_id, team):
    """Get player's history against specific team"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = data_fetcher.get_head_to_head(player_id, team, limit=limit)
        return jsonify({'games': history.to_dict('records')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get overall system statistics"""
    try:
        return jsonify({
            'total_players': len(cache['players']),
            'total_teams': len(cache['teams']),
            'last_update': cache['last_update'].isoformat() if cache['last_update'] else None,
            'predictions_today': 0,  # Would track actual predictions
            'active_users': 0  # Would track actual users
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team-stats')
def get_team_stats():
    """Get comprehensive team statistics"""
    try:
        team_name = request.args.get('team')
        season = request.args.get('season', '2024-25')

        conn = sqlite3.connect('../database/nba_data.db')
        cursor = conn.cursor()

        if team_name:
            # Get stats for specific team
            cursor.execute("""
                SELECT team_name, wins, losses,
                       offensive_rating, defensive_rating, net_rating, pace,
                       points_pg, field_goal_pct, three_point_pct, free_throw_pct,
                       assists_pg, rebounds_pg, turnovers_pg,
                       true_shooting_pct, effective_fg_pct,
                       opp_points_pg, opp_fg_pct, opp_three_pct,
                       efg_pct, fta_rate, tm_tov_pct, oreb_pct
                FROM team_stats
                WHERE team_name = ? AND season = ?
            """, (team_name, season))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return jsonify({'error': 'Team not found'}), 404

            return jsonify({
                'team': row[0],
                'record': {'wins': row[1], 'losses': row[2]},
                'ratings': {
                    'offensive': round(row[3], 1) if row[3] else 0,
                    'defensive': round(row[4], 1) if row[4] else 0,
                    'net': round(row[5], 1) if row[5] else 0,
                    'pace': round(row[6], 1) if row[6] else 0
                },
                'offense': {
                    'ppg': round(row[7], 1) if row[7] else 0,
                    'fg_pct': round(row[8], 3) if row[8] else 0,
                    'three_pct': round(row[9], 3) if row[9] else 0,
                    'ft_pct': round(row[10], 3) if row[10] else 0,
                    'apg': round(row[11], 1) if row[11] else 0,
                    'rpg': round(row[12], 1) if row[12] else 0,
                    'tov_pg': round(row[13], 1) if row[13] else 0
                },
                'advanced': {
                    'ts_pct': round(row[14], 3) if row[14] else 0,
                    'efg_pct': round(row[15], 3) if row[15] else 0
                },
                'defense': {
                    'opp_ppg': round(row[16], 1) if row[16] else 0,
                    'opp_fg_pct': round(row[17], 3) if row[17] else 0,
                    'opp_three_pct': round(row[18], 3) if row[18] else 0
                },
                'four_factors': {
                    'efg': round(row[19], 3) if row[19] else 0,
                    'fta_rate': round(row[20], 3) if row[20] else 0,
                    'tov_pct': round(row[21], 3) if row[21] else 0,
                    'oreb_pct': round(row[22], 3) if row[22] else 0
                }
            })
        else:
            # Get all teams
            cursor.execute("""
                SELECT team_name, offensive_rating, defensive_rating,
                       net_rating, pace, wins, losses
                FROM team_stats
                WHERE season = ?
                ORDER BY net_rating DESC
            """, (season,))

            rows = cursor.fetchall()
            conn.close()

            teams = []
            for row in rows:
                teams.append({
                    'team': row[0],
                    'off': round(row[1], 1) if row[1] else 0,
                    'def': round(row[2], 1) if row[2] else 0,
                    'net': round(row[3], 1) if row[3] else 0,
                    'pace': round(row[4], 1) if row[4] else 0,
                    'record': f"{row[5]}-{row[6]}"
                })

            return jsonify({'teams': teams, 'season': season})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize data on startup
    print("Initializing NBA Prediction System...")
    update_cache()
    print("Cache updated successfully!")

    # Get configuration from environment variables
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    print(f"\n{'='*50}")
    print(f"NBA Prediction System Server")
    print(f"{'='*50}")
    print(f"Server running on: http://localhost:{port}")
    print(f"API Documentation: http://localhost:{port}/api/health")
    print(f"Debug mode: {debug}")
    print(f"{'='*50}\n")

    # Run the Flask app
    app.run(debug=debug, host='0.0.0.0', port=port)
