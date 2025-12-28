import os
import sys
import asyncio
import types

import pytest

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


def test_kei_compare_auction_end_to_end():
    update = FakeUpdate()
    context = FakeContext(args=["compare", "auction", "Q2", "2025", "vs", "Q2", "2026"], bot=FakeBot())

    import asyncio
    asyncio.run(kei_command(update, context))

    last = update.message.last_reply
    assert last is not None, "Expected a reply from kei_command"
    text, mode = last
    assert "Q2 2025" in text and "Q2 2026" in text
    assert "Year-over-Year Change:" in text
    assert mode == "HTML"
