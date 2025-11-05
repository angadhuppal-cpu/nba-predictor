#!/usr/bin/env python3
"""
Test script to debug NBA API responses
"""
import requests
import pandas as pd

base_url = "https://stats.nba.com/stats"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Referer': 'https://stats.nba.com/'
}

print("Testing NBA Stats API...\n")

# Test 1: League Standings
print("=" * 60)
print("Test 1: League Standings")
print("=" * 60)
endpoint = 'leaguestandings'
params = {
    'LeagueID': '00',
    'Season': '2024-25',
    'SeasonType': 'Regular Season'
}

url = f"{base_url}/{endpoint}"
response = requests.get(url, headers=headers, params=params, timeout=30)

if response.status_code == 200:
    data = response.json()
    if 'resultSets' in data and len(data['resultSets']) > 0:
        headers_list = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']

        print(f"\nColumns returned: {headers_list}\n")

        df = pd.DataFrame(rows, columns=headers_list)
        print(f"Number of teams: {len(df)}")
        print(f"\nFirst few rows:")
        print(df.head(3))
        print(f"\nDataFrame columns: {df.columns.tolist()}")
else:
    print(f"Error: {response.status_code}")

print("\n")
