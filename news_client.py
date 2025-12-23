"""Lightweight news fetcher with short in-memory cache."""
import os
import time
from typing import List, Dict
import httpx

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
_cache: Dict[str, Dict] = {}
_CACHE_TTL = 600  # seconds


async def fetch_headlines(topic: str, country: str = "id", max_results: int = 4) -> List[Dict]:
    """Fetch top headlines for topic/country using NewsAPI.

    Returns list of dicts: {title, source, url, publishedAt}.
    Falls back to empty list on error or missing key.
    """
    if not NEWSAPI_KEY:
        return []

    topic_key = topic.lower().strip() or "general"
    cache_key = f"{country}:{topic_key}:{max_results}"
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached["ts"] < _CACHE_TTL:
        return cached["items"]

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWSAPI_KEY,
        "pageSize": max_results,
        "language": "en",
    }
    if country:
        params["country"] = country
    if topic_key and topic_key != "general":
        params["q"] = topic_key

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", [])
            items = [
                {
                    "title": a.get("title", ""),
                    "source": (a.get("source") or {}).get("name", ""),
                    "url": a.get("url", ""),
                    "publishedAt": a.get("publishedAt", ""),
                }
                for a in articles
                if a.get("title")
            ][:max_results]
            _cache[cache_key] = {"ts": now, "items": items}
            return items
    except Exception:
        return []


def format_headlines(items: List[Dict]) -> str:
    """Format headlines for LLM context."""
    if not items:
        return "No recent headlines available."
    lines = []
    for i, a in enumerate(items, 1):
        title = a.get("title", "").strip()
        src = a.get("source", "").strip()
        pub = a.get("publishedAt", "").strip()
        lines.append(f"{i}. {title} ({src}, {pub})")
    return "\n".join(lines)