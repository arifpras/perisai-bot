#!/usr/bin/env python3
"""
Test the complete /kei command handler for:
  /kei auction demand from q1 2025 to q4 2026

This simulates the full query processing including:
1. Pattern detection (quarter-to-quarter range)
2. Date parsing (Q1 2025 to Q4 2026)
3. Historical data loading (2025)
4. Forecast data loading (2026)
5. Table formatting
6. Response generation
"""

import sys
import os
import re
from datetime import date
from dateutil.relativedelta import relativedelta

# Add workspace to path
sys.path.insert(0, '/workspaces/perisai-bot')

# Import required functions
from telegram_bot import load_auction_period, format_auction_metrics_table, convert_markdown_code_fences_to_html

def parse_quarter_range_query(question):
    """Parse quarter-to-quarter range from question."""
    lower_q = question.lower()
    
    # Quarter-to-quarter range: "from q1 2025 to q4 2026"
    q_range = re.search(r"from\s+q([1-4])\s+(19\d{2}|20\d{2})\s+to\s+q([1-4])\s+(19\d{2}|20\d{2})", lower_q)
    if q_range:
        q1_txt, y1_txt, q2_txt, y2_txt = q_range.groups()
        q_start = int(q1_txt)
        y_start = int(y1_txt)
        q_end = int(q2_txt)
        y_end = int(y2_txt)
        
        periods = []
        year = y_start
        quarter = q_start
        while (year < y_end) or (year == y_end and quarter <= q_end):
            periods.append({'type': 'quarter', 'quarter': quarter, 'year': year})
            quarter += 1
            if quarter > 4:
                quarter = 1
                year += 1
        
        return periods
    
    return None

def main():
    """Test the /kei auction demand from q1 2025 to q4 2026 query."""
    
    question = "auction demand from q1 2025 to q4 2026"
    print("=" * 70)
    print(f"Testing: /kei {question}")
    print("=" * 70)
    
    # Step 1: Parse the query
    print("\n[Step 1] Parsing quarter-to-quarter range...")
    periods = parse_quarter_range_query(question)
    if not periods:
        print("❌ Failed to parse quarter range")
        return False
    
    print(f"✅ Parsed {len(periods)} quarters:")
    for p in periods:
        print(f"   - Q{p['quarter']} {p['year']}")
    
    # Step 2: Load auction data for each period
    print("\n[Step 2] Loading auction data for each period...")
    periods_data = []
    missing_labels = []
    
    for p in periods:
        pdata = load_auction_period(p)
        if pdata:
            periods_data.append(pdata)
            print(f"   ✅ Q{p['quarter']} {p['year']}: Loaded {len(pdata)} records")
        else:
            missing_labels.append(f"Q{p['quarter']} {p['year']}")
            print(f"   ⚠️  Q{p['quarter']} {p['year']}: No data (expected if forecast quarter)")
    
    print(f"\n   Total periods loaded: {len(periods_data)}")
    if missing_labels:
        print(f"   Missing/forecast periods: {', '.join(missing_labels)}")
    
    # Step 3: Format table
    print("\n[Step 3] Formatting auction metrics table...")
    if not periods_data:
        print("❌ No auction data found for requested range")
        return False
    
    try:
        table = format_auction_metrics_table(periods_data, ['incoming', 'awarded'])
        print("✅ Table formatted successfully")
        
        # Display formatted table
        note = ""
        if missing_labels:
            note = f"\n\n⚠️ Missing data for: {', '.join(missing_labels)}"
        
        response = table + note + "\n\n<blockquote>~ Kei</blockquote>"
        rendered = convert_markdown_code_fences_to_html(response)
        
        print("\n" + "=" * 70)
        print("TELEGRAM BOT RESPONSE:")
        print("=" * 70)
        print(rendered)
        print("=" * 70)
        
        return True
    except Exception as e:
        print(f"❌ Error formatting table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
