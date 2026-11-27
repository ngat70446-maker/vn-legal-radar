import json
import os
from email.utils import parsedate_to_datetime
from typing import Dict, List

import feedparser
from bs4 import BeautifulSoup

RSS_SOURCES = [
    {
        "name": "VnExpress Pháp luật",
        "url": "https://vnexpress.net/rss/phap-luat.rss",
    },
    {
        "name": "VnExpress Kinh doanh",
        "url": "https://vnexpress.net/rss/kinh-doanh.rss",
    },
]

DEFAULT_SEEN_PATH = os.path.join("data", "seen.json")
MAX_ARTICLES_PER_RUN = 5
MAX_SEEN_LINKS = 200


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and normalize whitespace from RSS description."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def load_seen(seen_path: str = DEFAULT_SEEN_PATH) -> List[str]:
    """Load list of previously sent article links from JSON file."""
    if not os.path.exists(seen_path):
        return []
    try:
        with open(seen_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [str(item) for item in data]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_seen(links: List[str], seen_path: str = DEFAULT_SEEN_PATH) -> None:
    """Persist sent article links to JSON, keeping at most MAX_SEEN_LINKS recent entries."""
    os.makedirs(os.path.dirname(seen_path), exist_ok=True)
    trimmed = links[-MAX_SEEN_LINKS:]
    with open(seen_path, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _parse_pub_timestamp(published: str) -> float:
    """Parse RFC 2822 date string into UNIX timestamp for sorting."""
    if not published:
        return 0.0
    try:
        return parsedate_to_datetime(published).timestamp()
    except (TypeError, ValueError):
        return 0.0


def fetch_new_articles(
    seen_links: List[str],
    limit: int = MAX_ARTICLES_PER_RUN,
) -> List[Dict[str, str]]:
    """Fetch RSS feeds, filter out seen links, and return up to `limit` newest articles."""
    seen_set = set(seen_links)
    collected: List[Dict[str, str]] = []
    batch_links = set()

    for source in RSS_SOURCES:
        feed = feedparser.parse(source["url"])
        if getattr(feed, "bozo", False) and not getattr(feed, "entries", None):
            print(f"[Fetcher] Warning: Failed to parse feed {source['name']}: {feed.bozo_exception}")
            continue

        for entry in feed.entries:
            link = entry.get("link", "").strip()
            if not link or link in seen_set or link in batch_links:
                continue

            title = clean_html(entry.get("title", "Không có tiêu đề"))
            description = clean_html(entry.get("description", ""))
            published = entry.get("published", "").strip()

            batch_links.add(link)
            collected.append(
                {
                    "title": title,
                    "link": link,
                    "description": description,
                    "published": published,
                    "source": source["name"],
                    "_ts": _parse_pub_timestamp(published),
                }
            )

    collected.sort(key=lambda item: item["_ts"], reverse=True)
    result = collected[:limit]
    for item in result:
        item.pop("_ts", None)
    return result
