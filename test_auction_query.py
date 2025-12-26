#!/usr/bin/env python3
"""
Debug test for "/kei auction demand 2026" example.
"""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from priceyield_20251223 import parse_intent, AuctionDB

def test_auction_query():
    print("=" * 70)
    print('TESTING: "/kei auction demand 2026"')
    print("=" * 70)
    print()
    
    # Step 1: Parse intent
    print("STEP 1: Parse Intent")
    print("-" * 70)
    query = "auction demand 2026"
    try:
        intent = parse_intent(query)
        print(f"✓ Query parsed successfully")
        print(f"  Type: {intent.type}")
        print(f"  Metric: {getattr(intent, 'metric', 'N/A')}")
        print(f"  Tenor: {getattr(intent, 'tenor', 'N/A')}")
        print(f"  Start Date: {getattr(intent, 'start_date', 'N/A')}")
        print(f"  End Date: {getattr(intent, 'end_date', 'N/A')}")
        print()
    except Exception as e:
        print(f"✗ Intent parsing failed: {type(e).__name__}: {e}")
        return False
    
    # Step 2: Load AuctionDB
    print("STEP 2: Load AuctionDB")
    print("-" * 70)
    try:
        auction_db = AuctionDB("20251224_auction_forecast.csv")
        print(f"✓ AuctionDB loaded successfully")
        print()
    except Exception as e:
        print(f"✗ AuctionDB load failed: {type(e).__name__}: {e}")
        return False
    
    # Step 3: Inspect database structure
    print("STEP 3: Inspect Database Structure")
    print("-" * 70)
    try:
        # Get all table names
        tables = auction_db.con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='memory'"
        ).fetchall()
        if tables:
            table_list = [t[0] for t in tables]
            print(f"✓ Available tables: {table_list}")
        else:
            print(f"⚠ No tables found via information_schema")
        
        # Try to get table info differently
        all_tables = auction_db.con.execute("SELECT * FROM duckdb_tables()").fetchall()
        if all_tables:
            print(f"  Alternative table list: {all_tables}")
        
        print()
    except Exception as e:
        print(f"⚠ Could not inspect tables: {type(e).__name__}: {e}")
    
    # Step 4: Try to query forecasts
    print("STEP 4: Query Forecast Table")
    print("-" * 70)
    try:
        result = auction_db.con.execute("SELECT * FROM forecasts LIMIT 1").fetchall()
        print(f"✓ forecasts table query succeeded")
        print(f"  Sample row: {result}")
        print()
    except Exception as e:
        print(f"✗ forecasts query failed: {type(e).__name__}: {e}")
        
        # Try alternative table names
        print("\n  Trying alternative table names...")
        alternatives = ["forecast", "auction_forecast", "data", "auction_data"]
        for alt_table in alternatives:
            try:
                result = auction_db.con.execute(f"SELECT * FROM {alt_table} LIMIT 1").fetchall()
                print(f"  ✓ Found table: {alt_table}")
                print(f"    Sample: {result}")
            except:
                pass
    
    # Step 5: Test AuctionDB.query_forecast()
    print("STEP 5: Test AuctionDB.query_forecast()")
    print("-" * 70)
    try:
        rows = auction_db.query_forecast(intent)
        print(f"✓ query_forecast() succeeded")
        print(f"  Rows returned: {len(rows)}")
        if rows:
            print(f"  Sample row: {rows[0]}")
        print()
    except Exception as e:
        print(f"✗ query_forecast() failed: {type(e).__name__}: {e}")
        
        # Inspect AuctionDB source code
        import inspect
        print("\n  AuctionDB.query_forecast() source:")
        try:
            source = inspect.getsource(auction_db.query_forecast)
            print(source[:500])  # First 500 chars
        except:
            pass

if __name__ == "__main__":
    test_auction_query()
