#!/usr/bin/env python3
"""Test exact scenario: 'price 10 year in august 2025'"""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from priceyield_20251223 import BondDB, parse_intent
from datetime import date

db = BondDB('/workspaces/perisai-bot/20251215_priceyield.csv')

query = "price 10 year in august 2025"
intent = parse_intent(query)

print(f"Query: '{query}'")
print(f"Metric: {intent.metric}")
print(f"Tenor: {intent.tenor}")
print(f"Period: {intent.start_date} to {intent.end_date}")
print()

# Fetch data like the bot would
params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
where = 'obs_date BETWEEN ? AND ?'
if intent.tenor:
    where += ' AND tenor = ?'
    params.append(intent.tenor)

print(f"Query where clause: {where}")
print(f"Params: {params}")
print()

rows = db.con.execute(
    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
    params
).fetchall()

print(f"Found {len(rows)} rows")
print()

# Show first few rows with both price and yield
for i, r in enumerate(rows[:5]):
    series, tenor, date_val, price, yield_val = r
    print(f"Row {i}: {series} {tenor} {date_val} → Price: {price:.2f}, Yield: {yield_val:.4f}%")

print("\nFor metric='price', we should be displaying the 'price' column")
print("For metric='yield', we should be displaying the 'yield' column")
print()
print(f"Current intent.metric = '{intent.metric}'")
print(f"Should format_rows_for_telegram use 'price' column? {intent.metric == 'price'}")
