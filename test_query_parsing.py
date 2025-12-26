#!/usr/bin/env python3
"""Test query parsing"""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

# Import directly from module
import importlib.util
spec = importlib.util.spec_from_file_location("bonddb", "/workspaces/perisai-bot/priceyield_20251223.py")
bonddb = importlib.util.module_from_spec(spec)

# Load without executing __main__
import os
os.environ['NO_CLI'] = '1'
spec.loader.exec_module(bonddb)

test_queries = [
    'compare price 5 year and 10 year in 2025',
    'plot 5 year and 10 year 2024',
    'chart yield 10 year 2025',
    'plot yield 5 year 2025',
    'chart yield 5 year and 10 year June 2025',
    'yield 5 year 2025',
    'price 5 year and 10 year 2025',
]

print('Testing query patterns:\n')
for query in test_queries:
    intent = bonddb.parse_intent(query)
    print(f'Query: "{query}"')
    print(f'  Type: {intent.type}')
    print(f'  Metric: {intent.metric}')
    print(f'  Tenor: {intent.tenor}')
    print(f'  Tenors: {intent.tenors}')
    if hasattr(intent, 'start_date') and intent.start_date:
        print(f'  Dates: {intent.start_date} to {intent.end_date}')
    print()
