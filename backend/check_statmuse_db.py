#!/usr/bin/env python3
"""Check what StatMuse data is in the database"""
import sqlite3

conn = sqlite3.connect('../database/nba_data.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT player_name, data_type, COUNT(*) as count
    FROM statmuse_data
    GROUP BY player_name, data_type
    ORDER BY player_name, data_type
''')

results = cursor.fetchall()

print('StatMuse Data in Database:')
print('='*70)
print(f"{'Player':<30} {'Data Type':<25} {'Records'}")
print('-'*70)

for player, dtype, count in results:
    print(f"{player:<30} {dtype:<25} {count}")

print('='*70)
print(f"Total: {len(results)} data entries")

conn.close()
