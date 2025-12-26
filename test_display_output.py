#!/usr/bin/env python3
"""Test the actual display for the range query scenario."""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from priceyield_20251223 import BondDB, parse_intent
from telegram_bot import format_rows_for_telegram
from datetime import date
import statistics

db = BondDB('/workspaces/perisai-bot/20251215_priceyield.csv')

query = "price 10 year in august 2025"
intent = parse_intent(query)

print(f"Query: '{query}'")
print(f"Metric: {intent.metric}")
print()

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

# Test statistics calculation
metric_values = [r.get(intent.metric) for r in rows_list if r.get(intent.metric) is not None]

print(f"Found {len(metric_values)} metric values")
print(f"Values: {metric_values}")
print()

if metric_values:
    min_val = min(metric_values)
    max_val = max(metric_values)
    avg_val = statistics.mean(metric_values)
    std_val = statistics.stdev(metric_values) if len(metric_values) > 1 else 0
    
    stat_label = intent.metric.capitalize() if hasattr(intent, 'metric') else 'Yield'
    
    print(f"Statistics Block:")
    print(f"<b>Summary ({stat_label})</b>")
    print("<pre>")
    print(f"Records : {len(metric_values):>5}")
    print(f"Period  : {intent.start_date} to {intent.end_date}")
    print(f"Min     : {min_val:>7.2f}{'%' if stat_label.lower()=='yield' else ''}")
    print(f"Max     : {max_val:>7.2f}{'%' if stat_label.lower()=='yield' else ''}")
    print(f"Average : {avg_val:>7.2f}{'%' if stat_label.lower()=='yield' else ''}")
    print(f"Std Dev : {std_val:>7.2f}{'%' if stat_label.lower()=='yield' else ''}")
    print("</pre>")
    print()
    
print(f"Data table (metric={intent.metric}):")
print(format_rows_for_telegram(rows_list, include_date=True, metric=intent.metric))
