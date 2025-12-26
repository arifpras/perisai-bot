#!/usr/bin/env python3
"""
Sanity check: Test all examples from examples_text to ensure they work correctly.
Tests intent parsing and basic query execution.
"""

import sys
import os
from datetime import datetime, timedelta

# Add workspace to path
sys.path.insert(0, '/workspaces/perisai-bot')

# Test examples from examples_text
EXAMPLES = {
    "/kei (Quant Analyst)": [
        "/kei yield 10 year 2025",
        "/kei plot yield 10 year 2025",
        "/kei forecast yield 10 year 2026-01-15",
        "/kei 5 and 10 years 2024",
    ],
    "/kin (Macro Strategist)": [
        "/kin what is fiscal policy",
        "/kin auction demand 2026",
        "/kin show 5 year 2024",
    ],
    "/both (Combined Analysis)": [
        "/both 5 and 10 years 2024",
        "/both compare yields 2024 vs 2025",
    ],
    "/check (Quick Lookup)": [
        "/check 2025-12-12 10 year",
        "/check price 5 and 10 years 6 Dec 2024",
    ],
}

def test_intent_parsing():
    """Test that all /kei, /kin, /both examples parse intent correctly."""
    from priceyield_20251223 import parse_intent
    
    print("=" * 60)
    print("TESTING INTENT PARSING")
    print("=" * 60)
    
    test_queries = [
        ("yield 10 year 2025", "RANGE or POINT with tenor & metric"),
        ("plot yield 10 year 2025", "RANGE with plot keyword"),
        ("forecast yield 10 year 2026-01-15", "POINT with forecast & date"),
        ("5 and 10 years 2024", "RANGE with multi-tenor"),
        ("what is fiscal policy", "General question (no bond data)"),
        ("auction demand 2026", "AUCTION_FORECAST intent"),
        ("show 5 year 2024", "RANGE with show keyword"),
        ("compare yields 2024 vs 2025", "RANGE with compare keyword"),
        ("2025-12-12 10 year", "POINT lookup"),
        ("price 5 and 10 years 6 Dec 2024", "POINT with multi-tenor"),
    ]
    
    passed = 0
    failed = 0
    
    for query, description in test_queries:
        try:
            intent = parse_intent(query)
            print(f"✓ PASS: {query}")
            print(f"        Intent: {intent.type}")
            if hasattr(intent, 'metric'):
                print(f"        Metric: {intent.metric}")
            if hasattr(intent, 'tenor'):
                print(f"        Tenor: {intent.tenor}")
            if hasattr(intent, 'tenors') and intent.tenors:
                print(f"        Tenors: {intent.tenors}")
            passed += 1
        except Exception as e:
            print(f"✗ FAIL: {query}")
            print(f"        Error: {type(e).__name__}: {e}")
            failed += 1
        print()
    
    print(f"\nIntent Parsing Summary: {passed} passed, {failed} failed")
    return passed, failed

def test_bond_db_access():
    """Test that BondDB can be accessed and queried."""
    print("=" * 60)
    print("TESTING BOND DATABASE ACCESS")
    print("=" * 60)
    
    try:
        from priceyield_20251223 import BondDB
        csv_path = "/workspaces/perisai-bot/20251215_priceyield.csv"
        
        if not os.path.exists(csv_path):
            print(f"✗ FAIL: CSV file not found at {csv_path}")
            return 0, 1
        
        db = BondDB(csv_path)
        print(f"✓ PASS: BondDB initialized successfully")
        
        # Test a simple query
        result = db.con.execute("SELECT COUNT(*) as count FROM ts").fetchone()
        count = result[0] if result else 0
        print(f"        Database has {count} bond price records")
        
        # Check tenors available
        tenors = db.con.execute("SELECT DISTINCT tenor FROM ts ORDER BY tenor").fetchall()
        tenor_list = [t[0] for t in tenors]
        print(f"        Available tenors: {tenor_list}")
        
        return 1, 0
    except Exception as e:
        print(f"✗ FAIL: BondDB access failed")
        print(f"        Error: {type(e).__name__}: {e}")
        return 0, 1

def test_auction_db_access():
    """Test that AuctionDB can be accessed."""
    print("=" * 60)
    print("TESTING AUCTION DATABASE ACCESS")
    print("=" * 60)
    
    try:
        from priceyield_20251223 import AuctionDB
        csv_path = "/workspaces/perisai-bot/20251224_auction_forecast.csv"
        
        if not os.path.exists(csv_path):
            print(f"⚠ WARNING: Auction CSV not found at {csv_path}")
            return 0, 0
        
        db = AuctionDB(csv_path)
        print(f"✓ PASS: AuctionDB initialized successfully")
        
        # Test a simple query
        result = db.con.execute("SELECT COUNT(*) as count FROM forecasts").fetchone()
        count = result[0] if result else 0
        print(f"        Database has {count} auction forecast records")
        
        return 1, 0
    except Exception as e:
        print(f"✗ FAIL: AuctionDB access failed")
        print(f"        Error: {type(e).__name__}: {e}")
        return 0, 1

def test_imports():
    """Test that all necessary imports work."""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    imports_to_test = [
        ("priceyield_20251223", ["BondDB", "AuctionDB", "parse_intent"]),
        ("telegram_bot", ["get_db", "get_auction_db", "ask_kei", "ask_kin"]),
        ("metrics", ["log_query"]),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, items in imports_to_test:
        try:
            module = __import__(module_name)
            for item in items:
                if not hasattr(module, item):
                    print(f"✗ FAIL: {module_name}.{item} not found")
                    failed += 1
                else:
                    print(f"✓ PASS: {module_name}.{item}")
                    passed += 1
        except ImportError as e:
            print(f"✗ FAIL: Cannot import {module_name}")
            print(f"        Error: {e}")
            failed += len(items)
        print()
    
    print(f"Import Summary: {passed} passed, {failed} failed")
    return passed, failed

def main():
    """Run all sanity checks."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " PERISAI-BOT EXAMPLES SANITY CHECK ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Imports
    p, f = test_imports()
    total_passed += p
    total_failed += f
    
    # Test 2: Bond DB
    p, f = test_bond_db_access()
    total_passed += p
    total_failed += f
    
    # Test 3: Auction DB
    p, f = test_auction_db_access()
    total_passed += p
    total_failed += f
    
    # Test 4: Intent Parsing
    p, f = test_intent_parsing()
    total_passed += p
    total_failed += f
    
    # Final summary
    print()
    print("=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"✓ Total Passed: {total_passed}")
    print(f"✗ Total Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n✅ ALL SANITY CHECKS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_failed} CHECK(S) FAILED - REVIEW ABOVE")
        return 1

if __name__ == "__main__":
    exit(main())
