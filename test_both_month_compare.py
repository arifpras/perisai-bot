#!/usr/bin/env python3
"""Test /both command month comparison (May 2025 vs Jun 2025)."""

import os
import sys
import asyncio

# Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from telegram_bot import (
    load_auction_period,
    format_auction_comparison_general,
    parse_auction_compare_query,
)


def test_parse_month_comparison():
    """Test that parse_auction_compare_query parses 'compare May 2025 vs Jun 2025'."""
    result = parse_auction_compare_query('compare May 2025 vs Jun 2025')
    assert result is not None
    assert len(result) == 2
    assert result[0]['type'] == 'month'
    assert result[0]['month'] == 5
    assert result[0]['year'] == 2025
    assert result[1]['type'] == 'month'
    assert result[1]['month'] == 6
    assert result[1]['year'] == 2025
    print("✓ parse_auction_compare_query correctly detects May 2025 vs Jun 2025")


def test_load_month_data():
    """Test that we can load May and Jun 2025 data."""
    may_period = {'type': 'month', 'month': 5, 'year': 2025}
    jun_period = {'type': 'month', 'month': 6, 'year': 2025}
    
    may_data = load_auction_period(may_period)
    jun_data = load_auction_period(jun_period)
    
    assert may_data is not None, "May 2025 data should exist"
    assert jun_data is not None, "Jun 2025 data should exist"
    
    # Check structure
    assert 'total_incoming' in may_data
    assert 'total_incoming' in jun_data
    assert 'monthly' in may_data
    assert 'monthly' in jun_data
    
    print(f"✓ May 2025 data loaded: Rp {may_data['total_incoming']:.2f}T")
    print(f"✓ Jun 2025 data loaded: Rp {jun_data['total_incoming']:.2f}T")
    
    return may_data, jun_data


def test_format_comparison():
    """Test that format_auction_comparison_general formats May vs Jun correctly."""
    may_data, jun_data = test_load_month_data()
    
    html = format_auction_comparison_general([may_data, jun_data])
    
    # Check that both months are in the output
    assert 'May 2025' in html, "Output should contain 'May 2025'"
    assert 'Jun 2025' in html, "Output should contain 'Jun 2025'"
    
    # Check that it's not full-year 2025
    assert '2025 Auction Demand:' not in html or 'May 2025 Auction Demand' in html, \
        "Output should show May/Jun months, not full year 2025"
    
    # Check for monthly breakdown (should have individual month lines)
    assert 'May' in html or 'Jun' in html, "Should include month names in comparison"
    
    print("✓ format_auction_comparison_general produces correct month labels")
    print("\nSample HTML output (first 500 chars):")
    print(html[:500])
    print("...")
    

if __name__ == '__main__':
    print("Testing /both month comparison support...\n")
    test_parse_month_comparison()
    test_format_comparison()
    print("\n✅ All tests passed!")
