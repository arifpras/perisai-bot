#!/usr/bin/env python3
"""
Test all example prompts from /examples command
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add workspace to path
sys.path.insert(0, '/workspaces/perisai-bot')

from priceyield_20251223 import BondDB, AuctionDB, parse_intent

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def test_parse_intent(query, expected_type=None):
    """Test if a query can be parsed"""
    try:
        intent = parse_intent(query)
        status = True
        msg = f"{GREEN}✅{RESET} Parsed as {intent.type}"
        if expected_type and intent.type != expected_type:
            status = False
            msg = f"{RED}✗{RESET} Expected {expected_type}, got {intent.type}"
        return status, msg
    except Exception as e:
        return False, f"{RED}✗{RESET} Parse error: {type(e).__name__}: {str(e)[:80]}"

def test_intent_fields(query, fields_to_check):
    """Test if parsed intent has expected fields"""
    try:
        intent = parse_intent(query)
        results = {}
        for field in fields_to_check:
            val = getattr(intent, field, None)
            results[field] = "✓" if val is not None else "✗"
        return True, results
    except Exception as e:
        return False, f"Error: {str(e)[:60]}"

def main():
    print(f"\n{BOLD}{BLUE}TESTING EXAMPLE PROMPTS FROM /examples{RESET}\n")
    
    # All examples from the /examples command
    examples = {
        "/kei Examples": [
            ("yield 10 year 2025", "RANGE"),  # Full year is a RANGE, not a POINT
            ("forecast yield 10 year 2026-01-15", "POINT"),
            ("auction demand 2026", "AUCTION_FORECAST"),
            ("yield 10 year 2025-12-27", "POINT"),  # Single date is a POINT
        ],
        "/kin Examples": [
            ("plot yield 10 year Jan 2025", "RANGE"),
            # General knowledge queries don't parse intent in /kin, they go directly to ask_kin
            # So we don't test them for intent parsing
        ],
        "/both Examples": [
            ("5 and 10 years 2024", "RANGE"),
            ("compare yields 2024 vs 2025", "RANGE"),
        ],
        "/check Examples": [
            ("2025-12-12 10 year", "POINT"),
            ("price 5 and 10 years 6 Dec 2024", "POINT"),
        ],
        "Auto-Redirect Examples": [
            ("plot 5 and 10 year", "RANGE"),  # /kei plot
            ("auction demand", "AUCTION_FORECAST"),  # /kin quantitative
        ],
    }
    
    total_tests = 0
    passed = 0
    failed = []
    
    for category, prompts in examples.items():
        print(f"{BOLD}{category}{RESET}")
        
        for query, expected_type in prompts:
            total_tests += 1
            status, msg = test_parse_intent(query, expected_type)
            
            # Display test
            symbol = f"{GREEN}✅{RESET}" if status else f"{RED}✗{RESET}"
            print(f"  {symbol} {query:<50} {msg}")
            
            if status:
                passed += 1
            else:
                failed.append((category, query, msg))
        
        print()
    
    # Summary
    print(f"\n{BOLD}SUMMARY{RESET}")
    print(f"Total: {total_tests} | {GREEN}Passed: {passed}{RESET} | {RED}Failed: {len(failed)}{RESET}")
    
    if failed:
        print(f"\n{BOLD}{RED}FAILED TESTS:{RESET}")
        for category, query, msg in failed:
            print(f"  [{category}] {query}")
            print(f"    {msg}\n")
        return False
    else:
        print(f"\n{GREEN}{BOLD}✅ All example prompts parse successfully!{RESET}\n")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
