#!/usr/bin/env python3
"""Test metric parsing for various user queries."""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from priceyield_20251223 import parse_intent

# Test cases
test_queries = [
    "price 10 year in august 2025",
    "yield 10 year in august 2025",
    "10 year in august 2025",  # Should default to yield
    "show me prices for 5 year",
    "what are the yields for 10 year?",
]

for query in test_queries:
    intent = parse_intent(query)
    print(f"Query: '{query}'")
    print(f"  → metric: {intent.metric}")
    print(f"  → tenor: {intent.tenor}")
    print()
