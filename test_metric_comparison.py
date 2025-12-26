#!/usr/bin/env python3
"""Test both price and yield queries to confirm correct metric detection and display."""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from priceyield_20251223 import BondDB, parse_intent
from telegram_bot import format_rows_for_telegram
import statistics

db = BondDB('/workspaces/perisai-bot/20251215_priceyield.csv')

test_cases = [
    "price 10 year in august 2025",
    "yield 10 year in august 2025",
    "10 year in august 2025",  # Should default to yield
]

for query in test_cases:
    print("=" * 60)
    print(f"Query: '{query}'")
    print("=" * 60)
    
    intent = parse_intent(query)
    
    print(f"Parsed metric: {intent.metric}")
    print(f"Parsed tenor: {intent.tenor}")
    print()
    
    # Fetch data
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
    
    metric_values = [r.get(intent.metric) for r in rows_list if r.get(intent.metric) is not None]
    
    if metric_values:
        min_val = min(metric_values)
        max_val = max(metric_values)
        avg_val = statistics.mean(metric_values)
        
        stat_label = intent.metric.capitalize()
        
        print(f"Summary ({stat_label}):")
        print(f"  Records  : {len(metric_values)}")
        print(f"  Min      : {min_val:.2f}{'%' if stat_label.lower()=='yield' else ''}")
        print(f"  Max      : {max_val:.2f}{'%' if stat_label.lower()=='yield' else ''}")
        print(f"  Average  : {avg_val:.2f}{'%' if stat_label.lower()=='yield' else ''}")
        print()
        
        # Show first 3 values
        formatted = format_rows_for_telegram(rows_list[:3], include_date=True, metric=intent.metric)
        print(f"Sample data table (first 3 rows):")
        print(formatted)
    
    print()
