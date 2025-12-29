"""Test auction month-range queries (e.g., "from dec 2024 to jan 2025")."""
import re
from datetime import date
from dateutil.relativedelta import relativedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot import load_auction_period, format_auction_metrics_table


def test_month_range_dec2024_to_jan2025():
    """Test that month range 'from dec 2024 to jan 2025' loads both months and formats table."""
    question = 'incoming bid and awarded bid from dec 2024 to jan 2025'
    q_lower = question.lower()
    
    months_map = {
        'jan':1,'january':1,
        'feb':2,'february':2,
        'mar':3,'march':3,
        'apr':4,'april':4,
        'may':5,
        'jun':6,'june':6,
        'jul':7,'july':7,
        'aug':8,'august':8,
        'sep':9,'sept':9,'september':9,
        'oct':10,'october':10,
        'nov':11,'november':11,
        'dec':12,'december':12,
    }
    
    # Parse month range
    mon_range = re.search(
        r"from\s+(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+(19\d{2}|20\d{2})\s+to\s+(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+(19\d{2}|20\d{2})",
        q_lower
    )
    assert mon_range is not None, "Failed to parse month range"
    
    m1_txt, y1_txt, m2_txt, y2_txt = mon_range.groups()
    assert m1_txt == 'dec' and y1_txt == '2024'
    assert m2_txt == 'jan' and y2_txt == '2025'
    
    m1 = months_map[m1_txt]
    y1 = int(y1_txt)
    m2 = months_map[m2_txt]
    y2 = int(y2_txt)
    
    # Expand month range
    start_date = date(y1, m1, 1)
    end_date = date(y2, m2, 1)
    periods = []
    current = start_date
    while current <= end_date:
        periods.append({'type': 'month', 'month': current.month, 'year': current.year})
        current += relativedelta(months=1)
    
    assert len(periods) == 2, f"Expected 2 periods, got {len(periods)}"
    assert periods[0] == {'type': 'month', 'month': 12, 'year': 2024}
    assert periods[1] == {'type': 'month', 'month': 1, 'year': 2025}
    
    # Load data for each month
    periods_data = []
    for p in periods:
        pdata = load_auction_period(p)
        assert pdata is not None, f"No data for period {p}"
        periods_data.append(pdata)
    
    assert len(periods_data) == 2, f"Expected 2 periods loaded, got {len(periods_data)}"
    
    # Verify Dec 2024 data
    dec_data = periods_data[0]
    assert dec_data['year'] == 2024
    assert dec_data['month'] == 12
    assert dec_data['total_incoming'] > 0, "Dec 2024 should have incoming bids"
    
    # Verify Jan 2025 data
    jan_data = periods_data[1]
    assert jan_data['year'] == 2025
    assert jan_data['month'] == 1
    assert jan_data['total_incoming'] > 0, "Jan 2025 should have incoming bids"
    
    # Format table
    metrics_list = ['incoming', 'awarded']
    table = format_auction_metrics_table(periods_data, metrics_list)
    
    assert 'Dec 2024' in table, "Table should contain 'Dec 2024'"
    assert 'Jan 2025' in table, "Table should contain 'Jan 2025'"
    assert 'Incoming' in table, "Table should contain 'Incoming' column"
    assert 'Awarded' in table, "Table should contain 'Awarded' column"
    assert 'Rp' in table, "Table should use Rp currency"
    
    print("✅ Test passed: Month range Dec 2024 to Jan 2025 loads correctly")
    print(f"\nFormatted table:\n{table}")


def test_month_range_across_year_boundary():
    """Test month range spanning year boundary (Nov 2024 to Feb 2025)."""
    question = 'from nov 2024 to feb 2025'
    q_lower = question.lower()
    
    months_map = {
        'jan':1,'january':1,
        'feb':2,'february':2,
        'mar':3,'march':3,
        'apr':4,'april':4,
        'may':5,
        'jun':6,'june':6,
        'jul':7,'july':7,
        'aug':8,'august':8,
        'sep':9,'sept':9,'september':9,
        'oct':10,'october':10,
        'nov':11,'november':11,
        'dec':12,'december':12,
    }
    
    mon_range = re.search(
        r"from\s+(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+(19\d{2}|20\d{2})\s+to\s+(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+(19\d{2}|20\d{2})",
        q_lower
    )
    assert mon_range is not None
    
    m1_txt, y1_txt, m2_txt, y2_txt = mon_range.groups()
    m1 = months_map[m1_txt]
    y1 = int(y1_txt)
    m2 = months_map[m2_txt]
    y2 = int(y2_txt)
    
    # Expand month range
    start_date = date(y1, m1, 1)
    end_date = date(y2, m2, 1)
    periods = []
    current = start_date
    while current <= end_date:
        periods.append({'type': 'month', 'month': current.month, 'year': current.year})
        current += relativedelta(months=1)
    
    # Should expand to: Nov 2024, Dec 2024, Jan 2025, Feb 2025
    assert len(periods) == 4, f"Expected 4 periods, got {len(periods)}"
    assert periods[0] == {'type': 'month', 'month': 11, 'year': 2024}
    assert periods[1] == {'type': 'month', 'month': 12, 'year': 2024}
    assert periods[2] == {'type': 'month', 'month': 1, 'year': 2025}
    assert periods[3] == {'type': 'month', 'month': 2, 'year': 2025}
    
    # Load all periods
    periods_data = []
    for p in periods:
        pdata = load_auction_period(p)
        if pdata:
            periods_data.append(pdata)
    
    assert len(periods_data) >= 2, f"Expected at least 2 periods with data, got {len(periods_data)}"
    
    # Format table
    metrics_list = ['incoming', 'awarded']
    table = format_auction_metrics_table(periods_data, metrics_list)
    
    print(f"✅ Test passed: Month range Nov 2024 to Feb 2025 loads {len(periods_data)} periods")
    print(f"\nFormatted table:\n{table}")


if __name__ == '__main__':
    test_month_range_dec2024_to_jan2025()
    test_month_range_across_year_boundary()
