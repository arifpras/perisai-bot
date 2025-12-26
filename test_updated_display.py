#!/usr/bin/env python3
"""Test the updated statistics display format with actual bot code."""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from priceyield_20251223 import BondDB, parse_intent
from datetime import date
import statistics

db = BondDB('/workspaces/perisai-bot/20251215_priceyield.csv')

query = "price 10 year in august 2025"
intent = parse_intent(query)

# Fetch data like the bot would
params = [intent.start_date.isoformat(), intent.end_date.isoformat()]
where = 'obs_date BETWEEN ? AND ?'
if intent.tenor:
    where += ' AND tenor = ?'
    params.append(intent.tenor)

rows = db.con.execute(
    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
    params
).fetchall()

rows_list = [
    dict(
        series=r[0],
        tenor=r[1],
        date=r[2].isoformat(),
        price=round(r[3], 2) if r[3] is not None else None,
        **{'yield': round(r[4], 2) if r[4] is not None else None}
    )
    for r in rows
]

# Test statistics calculation - UPDATED CODE
metric_values = [r.get(intent.metric) for r in rows_list if r.get(intent.metric) is not None]

response_text = f"📊 *Found {len(rows_list)} records*\n"
response_text += f"Period: {intent.start_date} → {intent.end_date}\n"

if metric_values:
    min_val = min(metric_values)
    max_val = max(metric_values)
    avg_val = statistics.mean(metric_values)
    std_val = statistics.stdev(metric_values) if len(metric_values) > 1 else 0
    # Economist-style summary block (minimalist)
    stat_label = intent.metric.capitalize() if hasattr(intent, 'metric') else 'Yield'
    response_text += f"\n<b>Summary ({stat_label})</b>\n"
    response_text += "<pre>"
    response_text += f"Records  : {len(metric_values):>5}\n"
    response_text += f"Min      : {min_val:>7.2f}{'%' if stat_label.lower()=='yield' else ''}\n"
    response_text += f"Max      : {max_val:>7.2f}{'%' if stat_label.lower()=='yield' else ''}\n"
    response_text += f"Average  : {avg_val:>7.2f}{'%' if stat_label.lower()=='yield' else ''}\n"
    response_text += f"Std Dev  : {std_val:>7.2f}{'%' if stat_label.lower()=='yield' else ''}"
    response_text += "</pre>\n"

print("Display Output:")
print("=" * 50)
print(response_text)
