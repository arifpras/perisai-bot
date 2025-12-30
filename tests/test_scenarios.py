import os
import sys
import asyncio
import pytest

# Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import telegram_bot as bot


class FakeUser:
    def __init__(self, id=12345, username="tester"):
        self.id = id
        self.username = username


class FakeMessage:
    def __init__(self):
        self.from_user = FakeUser()
        self.chat_id = 999
        self._replies = []
        self._photos = []
        self._documents = []

    async def reply_text(self, text, parse_mode=None):
        self._replies.append((text, parse_mode))

    async def reply_photo(self, photo=None, caption=None, parse_mode=None):
        self._photos.append((photo, caption, parse_mode))

    async def reply_document(self, document=None, filename=None, caption=None, parse_mode=None):
        self._documents.append((document, filename, caption, parse_mode))

    @property
    def last_reply(self):
        return self._replies[-1] if self._replies else None

    def any_response(self):
        return bool(self._replies or self._photos or self._documents)


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


@pytest.fixture(autouse=True)
def stub_llm(monkeypatch):
    async def fake_ask_kei(question, dual_mode=False):
        return "Stub Kei response\n\n<blockquote>~ Kei</blockquote>"

    async def fake_ask_kin(question, dual_mode=False):
        return "Stub Kin response\n\n<blockquote>~ Kin</blockquote>"

    async def fake_ask_kei_then_kin(question):
        return {
            "kei": "Stub Kei chain\n\n<blockquote>~ Kei</blockquote>",
            "kin": "Stub Kin chain\n\n<blockquote>~ Kin</blockquote>",
        }

    monkeypatch.setattr(bot, "ask_kei", fake_ask_kei)
    monkeypatch.setattr(bot, "ask_kin", fake_ask_kin)
    monkeypatch.setattr(bot, "ask_kei_then_kin", fake_ask_kei_then_kin)


SCENARIOS = [
    "/both auction demand from jan 2026 to dec 2026",
    "/both auction demand from q1 2026 to q4 2026",
    "/both auction demand in jan 2026",
    "/both auction demand in q2 2026",
    "/both auction demand in 2026",
    "/both auction demand trends 2023 to 2025",
    "/both auction demand trends 2020 to 2024",
    "/both auction demand trends 2018 to 2023",
    "/both forecast 10 year yield in the next 2 obs",
    "/both forecast 5 year yield in the next 10 obs",
    "/both forecast 20 year yield in the next 5 obs",
    "/both forecast incoming bid in q2 2026",
    "/both forecast awarded bid in q3 2026",
    "/both forecast bid-to-cover in q4 2026",
    "/both incoming bid and awarded bid from 2015 to 2021",
    "/both incoming bid and awarded bid from 2019 to 2021",
    "/both incoming bid and awarded bid from 2020 to 2024",
    "/both incoming bid and awarded bid from 2022 to 2026",
    "/both incoming bid in feb 2026",
    "/both incoming bid in mar 2026",
    "/both awarded bid in jan 2026",
    "/both awarded bid in q1 2026",
    "/both plot indonesia yield 5 year and 10 year from q3 2023 to q2 2024",
    "/both plot indonesia yield 5 year and 10 year from 2023 to 2025",
    "/both plot indonesia yield 5 year from oct 2024 to mar 2025",
    "/both tab incoming bid from jan 2026 to dec 2026",
    "/both tab awarded bid from jan 2025 to dec 2025",
    "/both tab incoming and awarded bid from 2020 to 2024",
    "/both compare yield 5 and 10 year 2024 vs 2025",
    "/both compare yield 5 and 10 year 2023 vs 2024",
    "/both compare price 5 and 10 year 2024 vs 2025",
    "/both compare yield 5 year and 20 year 2022 vs 2025",
    "/both yield 5 year from jan 2024 to dec 2024",
    "/both yield 10 year from q1 2024 to q4 2024",
    "/both yield 5 and 10 year from q3 2023 to q2 2024",
    "/both price 5 year from dec 2024 to jan 2025",
    "/both price 5 and 10 year from 2023 to 2024",
    "/both auction compare q2 2025 vs q2 2026",
    "/both auction compare May 2025 vs Jun 2025",
    "/both auction compare 2024 vs 2025",
    "/both auction forecast 2026",
    "/both auction forecast q1 2026",
    "/both bid-to-cover from 2020 to 2024",
    "/both bid-to-cover in 2026",
    "/check price 5 year 6 Dec 2024",
    "/check yield 5 year and 10 year 1 jan 2025",
    "/check yield 5 year and 10 year 5 dec 2024",
    "/check 2025-12-08 5 and 10 year",
    "/check price 10 year 2024-11-15",
    "/check yield 20 year 2025-01-10",
    "/kei auction demand from jan 2026 to dec 2026",
    "/kei auction demand from q1 2026 to q4 2026",
    "/kei auction demand in 2026",
    "/kei compare yield 5 and 10 year 2024 vs 2025",
    "/kei compare price 5 and 10 year 2024 vs 2025",
    "/kei incoming bid and awarded bid from dec 2010 to feb 2011",
    "/kei incoming bid and awarded bid from oct 2010 to feb 2011",
    "/kei incoming bid from jan 2026 to dec 2026",
    "/kei incoming bid in q1 2026",
    "/kei incoming bid in from q1 2026 to q3 2026",
    "/kei tab awarded bid from 2015 to 2024",
    "/kei tab incoming bid from 2020 to 2024",
    "/kei tab incoming bid from jan 2026 to dec 2026",
    "/kei tab incoming and awarded bid from 2022 to 2024",
    "/kei tab incoming and awarded bid from jan 2010 to dec 2011",
    "/kei tab yield 5 year and 10 year from dec 2023 to jan 2024",
    "/kei tab yield 5 year and 10 year q1 2023 to q3 2025",
    "/kei tab yield 5 and 10 year from q3 2023 to q2 2024",
    "/kei tab yield 5 year from dec 2024 to jan 2025",
    "/kei tab yield and price 5 year feb 2024",
    "/kei tab yield and price 5 year from 1 dec 2023 to 31 jan 2024",
    "/kei tab yield and price 5 year in feb 2025",
    "/kei tab price 5 year and 10 year from dec 2024 to jan 2025",
    "/kei tab price 5 year and 10 year in jan 2023",
    "/kei tab yield 5 year and 10 year in jan 2023",
    "/kei tab yield 5 year and 10 year from 2023 to 2024",
    "/kei tab price 5 year from q3 2023 to q2 2024",
    "/kei tab yield 20 year from 2022 to 2024",
    "/kei tab yield 15 year from jan 2024 to dec 2024",
    "/kei yield 5 year from dec 2023 to jan 2024",
    "/kei yield 10 year from oct 2024 to mar 2025",
    "/kei yield 5 and 10 year from 2023 to 2024",
    "/kei yield 5 year in feb 2025",
    "/kei price 5 year from 2024-12-01 to 2025-01-15",
    "/kin analyse incoming bid in q2 2026",
    "/kin analyse incoming bid in 2026",
    "/kin analyse awarded bid in 2026",
    "/kin plot indonesia yield 5 year and 10 year from q3 2023 to q2 2024",
    "/kin plot yield 5 and 10 year from oct 2024 to mar 2025",
    "/kin plot yield indonesia 5 year and 10 year dec 2024",
    "/kin plot yield indonesia 5 year and 10 year from dec 2024 to jan 2025",
    "/kin plot price 5 year from q3 2023 to q2 2024",
    "/kin plot price 10 year from 2023 to 2025",
    "/kin plot bid-to-cover from 2022 to 2024",
    "/kin who are you?",
    "/kei who are you?",
    "/kin buatkan pantun tentang pagi",
    "/kei buatkan pantun tentang pagi",
    "/both auction incoming bid 2025",
    "/both auction award bid 2025",
]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_scenarios_end_to_end(scenario):
    # Split command prefix and args
    parts = scenario.lstrip("/").split()
    if not parts:
        pytest.fail("Scenario had no command")
    command = parts[0].lower()
    args = parts[1:]

    update = FakeUpdate()
    context = FakeContext(args=args, bot=FakeBot())

    cmd_map = {
        "kei": bot.kei_command,
        "kin": bot.kin_command,
        "both": bot.both_command,
        "check": bot.check_command,
    }

    handler = cmd_map.get(command)
    assert handler is not None, f"No handler mapped for {command}"

    # Run the command
    asyncio.run(handler(update, context))

    assert update.message.any_response(), f"No response produced for scenario: {scenario}"

    # Basic sanity: ensure no empty text replies
    if update.message.last_reply:
        text, _mode = update.message.last_reply
        assert isinstance(text, str) and text.strip(), f"Empty reply for scenario: {scenario}"
