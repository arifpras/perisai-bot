import re
import math
import os
import sys

# Ensure project root is on PYTHONPATH for module imports
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from telegram_bot import get_historical_auction_data, format_auction_comparison


def approx_equal(a, b, tol=1e-2):
    return abs(a - b) <= tol


def test_historical_q2_2024_totals_and_btc():
    data = get_historical_auction_data(2024, 2)
    assert data is not None, "Expected historical data for Q2 2024"

    # Totals derived from auction_train.csv (converted to trillions):
    # Apr: 66.46750T, May: 129.03250T, Jun: 141.89470T
    expected_total = 66.46750 + 129.03250 + 141.89470
    assert approx_equal(data["total_incoming"], expected_total, tol=0.1)

    # Average bid-to-cover ~ 2.32x
    assert approx_equal(data["avg_bid_to_cover"], 2.32, tol=0.01)


def test_historical_q2_2025_totals_and_btc():
    data = get_historical_auction_data(2025, 2)
    assert data is not None, "Expected historical/derived data for Q2 2025"

    # Totals derived from auction_train.csv (converted to trillions):
    # Apr: 146.27590T, May: 241.29790T, Jun: 234.83160T
    expected_total = 146.27590 + 241.29790 + 234.83160
    assert approx_equal(data["total_incoming"], expected_total, tol=0.1)

    # Average bid-to-cover ~ 2.97x
    assert approx_equal(data["avg_bid_to_cover"], 2.97, tol=0.01)


def test_format_auction_comparison_contains_key_sections():
    hist = get_historical_auction_data(2024, 2)
    fut = get_historical_auction_data(2025, 2)
    assert hist and fut, "Comparison requires both periods"

    html = format_auction_comparison(hist, fut)

    # Key headers present
    assert "Q2 2024 Auction Demand" in html
    assert "Q2 2025 Auction Demand" in html

    # Contains totals and YoY change line
    assert "Total:" in html
    assert "Year-over-Year Change:" in html

    # YoY incoming change approximately +84.5%
    # Extract percentage from the line and compare
    m = re.search(r"Incoming bids:\s*([+\-]?[0-9.]+)%", html)
    assert m, "Expected YoY incoming percentage"
    yoy_pct = float(m.group(1))
    assert approx_equal(yoy_pct, 84.5, tol=0.2)
