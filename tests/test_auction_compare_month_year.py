import os
import sys
import re
import asyncio

# Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from telegram_bot import (
    get_historical_auction_month_data,
    get_historical_auction_year_data,
    format_auction_comparison_general,
    kei_command,
)


def approx_equal(a, b, tol=1e-2):
    return abs(a - b) <= tol


def test_month_loader_and_formatter_may_vs_jun_2025():
    may = get_historical_auction_month_data(2025, 5)
    jun = get_historical_auction_month_data(2025, 6)
    assert may and jun

    # Validate totals derived from auction_train.csv (converted to trillions)
    assert approx_equal(may["total_incoming"], 241.29790, tol=0.2)
    assert approx_equal(jun["total_incoming"], 234.83160, tol=0.2)

    html = format_auction_comparison_general([may, jun])
    assert "May 2025 Auction Demand" in html
    assert "Jun 2025 Auction Demand" in html
    assert "Change vs May 2025" in html


def test_year_loader_and_formatter_2024_vs_2025():
    y2024 = get_historical_auction_year_data(2024)
    y2025 = get_historical_auction_year_data(2025)
    assert y2024 and y2025

    # Totals should be positive and year labels present
    assert y2024["total_incoming"] > 0
    assert y2025["total_incoming"] > 0

    html = format_auction_comparison_general([y2024, y2025])
    assert "2024 Auction Demand" in html
    assert "2025 Auction Demand" in html
    assert "Change vs 2024" in html


# Minimal fakes reused from existing e2e test
class FakeUser:
    def __init__(self, id=12345, username="tester"):
        self.id = id
        self.username = username


class FakeMessage:
    def __init__(self):
        self.from_user = FakeUser()
        self.chat_id = 999
        self._replies = []

    async def reply_text(self, text, parse_mode=None):
        self._replies.append((text, parse_mode))

    @property
    def last_reply(self):
        return self._replies[-1] if self._replies else None


class FakeBot:
    async def send_chat_action(self, chat_id, action):
        return None


class FakeUpdate:
    def __init__(self):
        self.message = FakeMessage()


class FakeContext:
    def __init__(self, args, bot):
        self.args = args
        self.bot = bot


def test_kei_compare_months_end_to_end():
    update = FakeUpdate()
    context = FakeContext(args=["compare", "auction", "May", "2025", "vs", "Jun", "2025"], bot=FakeBot())
    asyncio.run(kei_command(update, context))

    last = update.message.last_reply
    assert last is not None
    text, mode = last
    assert "May 2025 Auction Demand" in text
    assert "Jun 2025 Auction Demand" in text
    assert "Change vs May 2025" in text
    assert mode == "HTML"


def test_kei_compare_years_end_to_end():
    update = FakeUpdate()
    context = FakeContext(args=["compare", "auction", "2024", "vs", "2025"], bot=FakeBot())
    asyncio.run(kei_command(update, context))

    last = update.message.last_reply
    assert last is not None
    text, mode = last
    assert "2024 Auction Demand" in text
    assert "2025 Auction Demand" in text
    assert "Change vs 2024" in text
    assert mode == "HTML"
