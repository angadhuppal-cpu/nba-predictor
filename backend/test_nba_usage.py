#!/usr/bin/env python3
"""Test NBA API usage rate fetching"""

from nba_data_fetcher import NBADataFetcher

fetcher = NBADataFetcher()

# Test fetching usage rate
usage_data = fetcher.get_player_usage_rate("Luka Dončić", season='2025-26')

if usage_data:
    print("Raw NBA API Response:")
    print(usage_data)
    print(f"\nUsage Rate Value: {usage_data.get('usage_rate')}")
    print(f"Type: {type(usage_data.get('usage_rate'))}")
else:
    print("No data returned")
