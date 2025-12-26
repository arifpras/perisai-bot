#!/usr/bin/env python3
"""Check what columns are actually available in the database."""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from priceyield_20251223 import BondDB

db = BondDB('/workspaces/perisai-bot/20251215_priceyield.csv')

# Check the schema
tables = db.con.execute("SELECT * FROM information_schema.tables WHERE table_schema='main'").fetchall()
print("Available tables:")
for t in tables:
    print(f"  {t}")

# Check what's in the ts table
columns = db.con.execute("PRAGMA table_info(ts)").fetchall()
print("\nts table columns:")
for col in columns:
    print(f"  {col}")

# Check a sample row
sample = db.con.execute("SELECT * FROM ts LIMIT 1").fetchall()
print("\nSample data:")
for row in sample:
    print(f"  {row}")

# Check for NULL values in price column
price_stats = db.con.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN price IS NOT NULL THEN 1 ELSE 0 END) as has_price,
        SUM(CASE WHEN "yield" IS NOT NULL THEN 1 ELSE 0 END) as has_yield
    FROM ts
""").fetchall()
print("\nPrice/Yield availability:")
for stat in price_stats:
    print(f"  {stat}")
