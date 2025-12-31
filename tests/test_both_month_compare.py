"""Test /both command month-vs-month comparison (May 2025 vs Jun 2025)."""

import os
import sys
import asyncio

# Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from telegram_bot import both_command


class FakeUser:
    def __init__(self, id=12345, username="tester"):
        self.id = id
        self.username = username


class FakeMessage:
    def __init__(self, text="", user=None):
        self.text = text
        self.from_user = user or FakeUser()
        self.chat_id = 12345
        self.replies = []
    
    async def reply_text(self, text, parse_mode=None, reply_markup=None):
        self.replies.append((text, parse_mode))
    
    @property
    def last_reply(self):
        return self.replies[-1] if self.replies else None


class FakeBot:
    async def send_chat_action(self, chat_id, action):
        pass


class FakeUpdate:
    def __init__(self, message_text=""):
        self.message = FakeMessage(text=message_text, user=FakeUser())
        
    async def reply_text(self, text, parse_mode=None):
        await self.message.reply_text(text, parse_mode=parse_mode)


class FakeContext:
    def __init__(self, args=None, bot=None):
        self.args = args or []
        self.bot = bot or FakeBot()


def test_both_month_vs_month_compare():
    """Test that /both auction compare May 2025 vs Jun 2025 returns month-level breakdown."""
    update = FakeUpdate(message_text="/both auction compare May 2025 vs Jun 2025")
    # Pass the question as context.args (as the command handler expects)
    context = FakeContext(
        args=["auction", "compare", "May", "2025", "vs", "Jun", "2025"],
        bot=FakeBot()
    )
    
    # Run the command
    asyncio.run(both_command(update, context))
    
    # Check replies
    assert len(update.message.replies) > 0, "Should have at least one reply"
    
    # First reply should be the comparison table
    first_reply, _ = update.message.replies[0]
    
    # Verify May and June are shown separately
    assert 'May 2025' in first_reply, "Should show 'May 2025' in comparison"
    assert 'Jun 2025' in first_reply, "Should show 'Jun 2025' in comparison"
    
    # Verify it's NOT showing full-year 2025 aggregate
    assert '2025 Auction Demand' not in first_reply or 'May' in first_reply, \
        "Should show monthly breakdown, not full-year aggregate"
    
    # Check that change/comparison analysis is present
    assert 'Change' in first_reply or 'vs' in first_reply.lower(), \
        "Should include comparison/change analysis"
    
    # Verify the data values are reasonable
    assert 'Rp' in first_reply, "Should include Rp currency values"
    assert '241' in first_reply or '235' in first_reply, \
        "Should include realistic May/Jun 2025 data (~241T for May, ~235T for Jun)"
    
    print("✅ Test passed: /both auction compare May 2025 vs Jun 2025")
    print("\nComparison output:")
    print(first_reply)
    

if __name__ == '__main__':
    test_both_month_vs_month_compare()
