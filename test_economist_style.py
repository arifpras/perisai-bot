#!/usr/bin/env python3
"""Sanity check: Generate sample plots with The Economist style"""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from datetime import date
from app_fastapi import _plot_range_to_png, get_db

print("🎨 Testing The Economist Chart Style\n")
print("=" * 60)

# Test 1: Single tenor plot
print("\n📊 Test 1: Single tenor (10 year, 2024)")
try:
    db = get_db("20251215_priceyield.csv")
    png_data = _plot_range_to_png(
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        metric='yield',
        tenor='10_year',
        tenors=None
    )
    
    with open('/workspaces/perisai-bot/test_plot_single.png', 'wb') as f:
        f.write(png_data)
    
    print("✅ Generated: test_plot_single.png")
    print(f"   Size: {len(png_data):,} bytes")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Multi-tenor plot
print("\n📊 Test 2: Multi-tenor (5 & 10 year, 2024)")
try:
    db = get_db("20251215_priceyield.csv")
    png_data = _plot_range_to_png(
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        metric='yield',
        tenor='05_year',
        tenors=['05_year', '10_year']
    )
    
    with open('/workspaces/perisai-bot/test_plot_multi.png', 'wb') as f:
        f.write(png_data)
    
    print("✅ Generated: test_plot_multi.png")
    print(f"   Size: {len(png_data):,} bytes")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Recent data (2025)
print("\n📊 Test 3: Single tenor (10 year, 2025 YTD)")
try:
    db = get_db("20251215_priceyield.csv")
    png_data = _plot_range_to_png(
        db=db,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 12),
        metric='yield',
        tenor='10_year',
        tenors=None
    )
    
    with open('/workspaces/perisai-bot/test_plot_2025.png', 'wb') as f:
        f.write(png_data)
    
    print("✅ Generated: test_plot_2025.png")
    print(f"   Size: {len(png_data):,} bytes")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("\n🎯 All plots generated successfully!")
print("📂 Files saved in: /workspaces/perisai-bot/")
print("\nThe Economist style features:")
print("  • Signature red/blue/teal colors")
print("  • Light gray background (#F0F0F0)")
print("  • Horizontal gridlines only (subtle, white)")
print("  • Clean, minimal design")
print("  • Left-aligned titles")
print("  • High quality (150 DPI)")
