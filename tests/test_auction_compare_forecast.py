import os
import sys
import math

# Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from priceyield_20251223 import AuctionDB
from telegram_bot import get_historical_auction_data, format_auction_comparison


def approx_equal(a, b, tol=1e-2):
    return abs(a - b) <= tol


def test_q2_2026_forecast_totals_and_btc():
    db = AuctionDB('database/20251224_auction_forecast.csv')

    # Collect rows for Q2 2026
    months = [4, 5, 6]
    rows = []
    for m in months:
        intent = type('obj', (object,), {
            'start_date': __import__('datetime').date(2026, m, 1),
            'end_date': __import__('datetime').date(2026, m, 28)
        })()
        rows.extend(db.query_forecast(intent))

    assert rows, "Expected forecast rows for Q2 2026"

    incoming_total = sum(r['incoming_billions'] for r in rows)
    btc_avg = sum(r['bid_to_cover'] for r in rows) / len(rows)

    # From CSV values: ~236.85 + 236.91 + 250.50 = 724.27T
    assert approx_equal(incoming_total, 724.27, tol=0.2)
    # Average bid-to-cover ~ 1.53x
    assert approx_equal(btc_avg, 1.53, tol=0.05)


def test_comparison_formatter_q2_2025_vs_q2_2026():
    hist = get_historical_auction_data(2025, 2)
    assert hist is not None

    # Build forecast_data dict from AuctionDB for Q2 2026
    db = AuctionDB('20251224_auction_forecast.csv')
    months = [4, 5, 6]
    monthly = []
    total_incoming = 0.0
    btc_vals = []
    for m in months:
        intent = type('obj', (object,), {
            'start_date': __import__('datetime').date(2026, m, 1),
            'end_date': __import__('datetime').date(2026, m, 28)
        })()
        rows = db.query_forecast(intent)
        for r in rows:
            monthly.append({
                'month': int(r['auction_month']),
                'incoming': r['incoming_billions'],
                'bid_to_cover': r['bid_to_cover']
            })
            total_incoming += r['incoming_billions']
            btc_vals.append(r['bid_to_cover'])

    forecast = {
        'year': 2026,
        'quarter': 2,
        'monthly': monthly,
        'total_incoming': total_incoming,
        'avg_bid_to_cover': sum(btc_vals) / len(btc_vals)
    }

    html = format_auction_comparison(hist, forecast)
    assert "Q2 2025 Auction Demand" in html
    assert "Q2 2026 Auction Demand" in html
    assert "Year-over-Year Change:" in html
