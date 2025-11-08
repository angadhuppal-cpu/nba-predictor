"""
StatMuse Web Scraper for Granular NBA Statistics
Fetches detailed player stats not easily available from official NBA API:
- Player vs specific opponent history
- Home/Away splits
- Recent form (last 5, 10, 15 games)
- Clutch time performance
- Month-by-month trends
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sqlite3
from datetime import datetime
import re
import json

class StatMuseScraper:
    """
    Scraper for StatMuse detailed statistics
    """

    def __init__(self, db_path='../database/nba_data.db'):
        self.base_url = 'https://www.statmuse.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        self.db_path = db_path
        self.rate_limit_delay = 2  # Seconds between requests (be respectful)

    def format_player_name(self, player_name):
        """Convert 'LeBron James' to 'lebron-james' for URL"""
        return player_name.lower().replace(' ', '-').replace("'", "")

    def format_team_name(self, team_name):
        """Convert 'Los Angeles Lakers' to 'lakers' for URL"""
        # Team name to URL format mapping
        team_url_map = {
            'Atlanta Hawks': 'hawks',
            'Boston Celtics': 'celtics',
            'Brooklyn Nets': 'nets',
            'Charlotte Hornets': 'hornets',
            'Chicago Bulls': 'bulls',
            'Cleveland Cavaliers': 'cavaliers',
            'Dallas Mavericks': 'mavericks',
            'Denver Nuggets': 'nuggets',
            'Detroit Pistons': 'pistons',
            'Golden State Warriors': 'warriors',
            'Houston Rockets': 'rockets',
            'Indiana Pacers': 'pacers',
            'LA Clippers': 'clippers',
            'Los Angeles Lakers': 'lakers',
            'Memphis Grizzlies': 'grizzlies',
            'Miami Heat': 'heat',
            'Milwaukee Bucks': 'bucks',
            'Minnesota Timberwolves': 'timberwolves',
            'New Orleans Pelicans': 'pelicans',
            'New York Knicks': 'knicks',
            'Oklahoma City Thunder': 'thunder',
            'Orlando Magic': 'magic',
            'Philadelphia 76ers': '76ers',
            'Phoenix Suns': 'suns',
            'Portland Trail Blazers': 'trail-blazers',
            'Sacramento Kings': 'kings',
            'San Antonio Spurs': 'spurs',
            'Toronto Raptors': 'raptors',
            'Utah Jazz': 'jazz',
            'Washington Wizards': 'wizards'
        }
        return team_url_map.get(team_name, team_name.lower().split()[-1])

    def fetch_player_vs_opponent(self, player_name, opponent_team, last_n_games=10):
        """
        Fetch player's performance vs specific opponent
        Example: LeBron James stats vs Warriors last 10 games
        """
        player_url = self.format_player_name(player_name)
        team_url = self.format_team_name(opponent_team)

        # StatMuse query format
        url = f"{self.base_url}/nba/ask/{player_url}-stats-vs-{team_url}-last-{last_n_games}-games"

        try:
            print(f"Fetching: {player_name} vs {opponent_team} (last {last_n_games} games)")
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                print(f"  ✗ Failed: HTTP {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the summary statistics (e.g., "LeBron James has averaged 28.5 points...")
            summary = self.extract_summary_stats(soup)

            # Extract game-by-game table
            games_data = self.extract_games_table(soup)

            if summary:
                print(f"  ✓ Found: {summary['games']} games, {summary['ppg']:.1f} PPG vs {opponent_team}")

            time.sleep(self.rate_limit_delay)  # Rate limiting

            return {
                'player': player_name,
                'opponent': opponent_team,
                'last_n_games': last_n_games,
                'summary': summary,
                'games': games_data,
                'fetched_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None

    def extract_summary_stats(self, soup):
        """Extract summary stats from StatMuse page"""
        try:
            # StatMuse typically has a headline with the summary
            headline = soup.find('h1') or soup.find('p', class_='nlg-answer')

            if not headline:
                return None

            text = headline.get_text()

            # Parse numbers from text like "LeBron James has averaged 28.5 points, 7.2 rebounds and 6.8 assists in 10 games"
            ppg_match = re.search(r'([\d.]+)\s+points', text)
            rpg_match = re.search(r'([\d.]+)\s+rebounds', text)
            apg_match = re.search(r'([\d.]+)\s+assists', text)
            games_match = re.search(r'in\s+(\d+)\s+games?', text)

            return {
                'ppg': float(ppg_match.group(1)) if ppg_match else 0,
                'rpg': float(rpg_match.group(1)) if rpg_match else 0,
                'apg': float(apg_match.group(1)) if apg_match else 0,
                'games': int(games_match.group(1)) if games_match else 0,
                'summary_text': text
            }

        except Exception as e:
            print(f"  ⚠ Could not parse summary: {e}")
            return None

    def extract_games_table(self, soup):
        """Extract game-by-game data table"""
        try:
            # Find the table with game logs
            table = soup.find('table')

            if not table:
                return []

            games = []
            rows = table.find_all('tr')[1:]  # Skip header

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 10:
                    game = {
                        'date': cols[1].get_text(strip=True) if len(cols) > 1 else '',
                        'opponent': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                        'min': cols[3].get_text(strip=True) if len(cols) > 3 else '',
                        'pts': int(cols[4].get_text(strip=True)) if len(cols) > 4 and cols[4].get_text(strip=True).isdigit() else 0,
                        'reb': int(cols[5].get_text(strip=True)) if len(cols) > 5 and cols[5].get_text(strip=True).isdigit() else 0,
                        'ast': int(cols[6].get_text(strip=True)) if len(cols) > 6 and cols[6].get_text(strip=True).isdigit() else 0,
                    }
                    games.append(game)

            return games

        except Exception as e:
            print(f"  ⚠ Could not parse games table: {e}")
            return []

    def fetch_home_away_splits(self, player_name, season='2025-26'):
        """
        Fetch player's home vs away splits
        """
        player_url = self.format_player_name(player_name)

        # Try both home and away queries
        stats = {}

        for location in ['home', 'away']:
            url = f"{self.base_url}/nba/ask/{player_url}-{location}-stats-this-season"

            try:
                print(f"Fetching: {player_name} {location} stats")
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    summary = self.extract_summary_stats(soup)

                    if summary:
                        stats[location] = summary
                        print(f"  ✓ {location.capitalize()}: {summary['ppg']:.1f} PPG")

                time.sleep(self.rate_limit_delay)

            except Exception as e:
                print(f"  ✗ Error fetching {location} stats: {e}")

        return {
            'player': player_name,
            'season': season,
            'home': stats.get('home', {}),
            'away': stats.get('away', {}),
            'fetched_at': datetime.now().isoformat()
        }

    def fetch_recent_form(self, player_name, last_n_games=5):
        """
        Fetch player's recent form (last N games)
        """
        player_url = self.format_player_name(player_name)
        url = f"{self.base_url}/nba/ask/{player_url}-last-{last_n_games}-games"

        try:
            print(f"Fetching: {player_name} last {last_n_games} games")
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                summary = self.extract_summary_stats(soup)
                games = self.extract_games_table(soup)

                if summary:
                    print(f"  ✓ Last {last_n_games}: {summary['ppg']:.1f} PPG")

                time.sleep(self.rate_limit_delay)

                return {
                    'player': player_name,
                    'last_n_games': last_n_games,
                    'summary': summary,
                    'games': games,
                    'fetched_at': datetime.now().isoformat()
                }

        except Exception as e:
            print(f"  ✗ Error: {e}")

        return None

    def fetch_clutch_stats(self, player_name, season='2025-26'):
        """
        Fetch clutch time performance (4th quarter stats)
        """
        player_url = self.format_player_name(player_name)
        url = f"{self.base_url}/nba/ask/{player_url}-4th-quarter-stats-this-season"

        try:
            print(f"Fetching: {player_name} 4th quarter/clutch stats")
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                summary = self.extract_summary_stats(soup)

                if summary:
                    print(f"  ✓ 4th Quarter: {summary['ppg']:.1f} PPG")

                time.sleep(self.rate_limit_delay)

                return {
                    'player': player_name,
                    'season': season,
                    'clutch_stats': summary,
                    'fetched_at': datetime.now().isoformat()
                }

        except Exception as e:
            print(f"  ✗ Error: {e}")

        return None

    def fetch_usage_rate(self, player_name, season='2025-26'):
        """
        Fetch player's usage rate from StatMuse
        """
        player_url = self.format_player_name(player_name)
        url = f"{self.base_url}/nba/ask/{player_url}-usage-rate-this-season"

        try:
            print(f"Fetching: {player_name} usage rate")
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract usage rate from page
                headline = soup.find('h1') or soup.find('p', class_='nlg-answer')

                if headline:
                    text = headline.get_text()
                    # Parse usage rate from text like "has a 28.5 usage rate"
                    usage_match = re.search(r'([\d.]+)\s*usage', text, re.IGNORECASE)

                    if usage_match:
                        usage_rate = float(usage_match.group(1))
                        print(f"  ✓ Usage Rate: {usage_rate}%")

                        time.sleep(self.rate_limit_delay)

                        return {
                            'player': player_name,
                            'season': season,
                            'usage_rate': usage_rate,
                            'source': 'StatMuse',
                            'fetched_at': datetime.now().isoformat()
                        }

        except Exception as e:
            print(f"  ✗ Error: {e}")

        return None

    def save_to_database(self, data, data_type):
        """Save scraped data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table for StatMuse data if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statmuse_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT,
                    data_type TEXT,
                    opponent TEXT,
                    data_json TEXT,
                    fetched_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Insert data
            cursor.execute('''
                INSERT INTO statmuse_data (player_name, data_type, opponent, data_json, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data.get('player'),
                data_type,
                data.get('opponent', ''),
                json.dumps(data),
                datetime.now()
            ))

            conn.commit()
            conn.close()
            print(f"  ✓ Saved to database: {data_type}")

        except Exception as e:
            print(f"  ✗ Database error: {e}")

    def fetch_comprehensive_player_stats(self, player_name, opponent_team=None):
        """
        Fetch all available granular stats for a player
        """
        print(f"\n{'='*70}")
        print(f"Fetching Comprehensive Stats for: {player_name}")
        print(f"{'='*70}\n")

        all_stats = {}

        # 1. Recent form (last 5 games)
        recent_form = self.fetch_recent_form(player_name, last_n_games=5)
        if recent_form:
            all_stats['recent_form_5'] = recent_form
            self.save_to_database(recent_form, 'recent_form_5')

        # 2. Home/Away splits
        splits = self.fetch_home_away_splits(player_name)
        if splits:
            all_stats['home_away_splits'] = splits
            self.save_to_database(splits, 'home_away_splits')

        # 3. Clutch stats
        clutch = self.fetch_clutch_stats(player_name)
        if clutch:
            all_stats['clutch_stats'] = clutch
            self.save_to_database(clutch, 'clutch_stats')

        # 4. If opponent specified, get matchup stats
        if opponent_team:
            matchup = self.fetch_player_vs_opponent(player_name, opponent_team, last_n_games=10)
            if matchup:
                all_stats['vs_opponent'] = matchup
                self.save_to_database(matchup, 'vs_opponent')

        print(f"\n{'='*70}")
        print(f"✓ Comprehensive stats fetched for {player_name}")
        print(f"{'='*70}\n")

        return all_stats


# Example usage
if __name__ == '__main__':
    scraper = StatMuseScraper()

    # Example: Fetch LeBron's stats vs Warriors
    stats = scraper.fetch_comprehensive_player_stats(
        player_name='LeBron James',
        opponent_team='Golden State Warriors'
    )

    print("\nFetched Stats:")
    print(json.dumps(stats, indent=2, default=str))
