import os
import time
from typing import Any, Dict

import requests

EMBED_COLOR_NAVY = 0x1E3A8A
RATE_LIMIT_DELAY_SECONDS = 1.5
REQUEST_TIMEOUT_SECONDS = 15


def build_embed_payload(article: Dict[str, str], summary: str) -> Dict[str, Any]:
    """Build a Discord Webhook JSON payload containing a single rich Embed."""
    source = article.get("source", "VnExpress")
    published = article.get("published", "") or "N/A"
    footer_text = f"{source} • {published}"

    embed = {
        "title": article.get("title", "Không có tiêu đề")[:256],
        "url": article.get("link", ""),
        "description": summary[:4096],
        "color": EMBED_COLOR_NAVY,
        "footer": {
            "text": footer_text[:2048],
        },
    }
    return {"embeds": [embed]}


def send_discord_notification(
    article: Dict[str, str],
    summary: str,
    sleep_after: bool = True,
) -> bool:
    """Send an article Embed to Discord Webhook. Returns True on success."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("[Notifier] DISCORD_WEBHOOK_URL is not set. Cannot send notification.")
        return False

    payload = build_embed_payload(article, summary)
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code in (200, 204):
            if sleep_after:
                time.sleep(RATE_LIMIT_DELAY_SECONDS)
            return True

        print(
            f"[Notifier] Discord returned HTTP {response.status_code}: {response.text}"
        )
        return False
    except requests.RequestException as exc:
        print(f"[Notifier] Failed to send Discord webhook: {exc}")
        return False
