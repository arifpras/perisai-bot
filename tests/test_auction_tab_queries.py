import os
import sys
import asyncio

# Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from telegram_bot import kei_command


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


def test_kei_tab_incoming_from_year_to_year():
    update = FakeUpdate()
    context = FakeContext(args=["tab", "incoming", "bid", "from", "2024", "to", "2025"], bot=FakeBot())
    asyncio.run(kei_command(update, context))

    last = update.message.last_reply
    assert last is not None
    text, mode = last
    assert "Period" in text and "Incoming" in text
    assert "2024" in text and "2025" in text
    from telegram.constants import ParseMode
    assert mode == ParseMode.MARKDOWN


def test_kei_tab_awarded_months_2026():
    update = FakeUpdate()
    context = FakeContext(args=["tab", "awarded", "bid", "from", "Apr", "2026", "to", "Jun", "2026"], bot=FakeBot())
    asyncio.run(kei_command(update, context))

    last = update.message.last_reply
    assert last is not None
    text, mode = last
    assert "Period" in text and "Awarded" in text
    # Month names presence depends on label formatting
    from telegram.constants import ParseMode
    assert mode == ParseMode.MARKDOWN


def test_kei_tab_incoming_and_awarded_quarters_2026():
    update = FakeUpdate()
    context = FakeContext(args=["tab", "incoming", "and", "awarded", "bid", "from", "Q2", "2026", "to", "Q3", "2026"], bot=FakeBot())
    asyncio.run(kei_command(update, context))

    last = update.message.last_reply
    assert last is not None
    text, mode = last
    assert "Period" in text and "Incoming" in text and "Awarded" in text
    from telegram.constants import ParseMode
    assert mode == ParseMode.MARKDOWN


def test_kei_tab_incoming_single_month_2025():
    update = FakeUpdate()
    context = FakeContext(args=["tab", "incoming", "bid", "in", "May", "2025"], bot=FakeBot())
    asyncio.run(kei_command(update, context))

    last = update.message.last_reply
    assert last is not None
    text, mode = last
    from telegram.constants import ParseMode
    assert "Period" in text and "Incoming" in text
    assert "May 2025" in text
    assert mode == ParseMode.MARKDOWN
