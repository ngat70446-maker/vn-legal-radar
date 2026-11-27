import argparse
import json
import sys

from src.fetcher import fetch_new_articles, load_seen, save_seen
from src.notifier import build_embed_payload, send_discord_notification
from src.summarizer import summarize_article


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vietnamese Legal & Business News Radar"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and summarize articles, print Discord Embed payloads, without sending or updating seen.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("[Step 1/4] Loading seen articles from data/seen.json...")
    seen_links = load_seen()
    print(f"          Loaded {len(seen_links)} seen link(s).")

    print("[Step 2/4] Fetching new articles from VnExpress RSS feeds...")
    new_articles = fetch_new_articles(seen_links)
    if not new_articles:
        print("          No new articles found. Exiting cleanly.")
        return 0

    print(f"          Found {len(new_articles)} new article(s).")

    print("[Step 3/4] Summarizing articles...")
    summarized = []
    for idx, article in enumerate(new_articles, start=1):
        print(f"          ({idx}/{len(new_articles)}) {article['title']}")
        summary = summarize_article(article)
        summarized.append((article, summary))

    if args.dry_run:
        print("[Step 4/4] --dry-run enabled: printing Embed payloads (no Discord send, no seen.json write).")
        for idx, (article, summary) in enumerate(summarized, start=1):
            payload = build_embed_payload(article, summary)
            print(f"\n--- Embed Payload #{idx} ---")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("\n[Done] Dry-run completed successfully.")
        return 0

    print("[Step 4/4] Sending notifications to Discord...")
    sent_links = []
    for idx, (article, summary) in enumerate(summarized):
        is_last = idx == len(summarized) - 1
        success = send_discord_notification(
            article,
            summary,
            sleep_after=not is_last,
        )
        if success:
            sent_links.append(article["link"])
            print(f"          Sent ({idx + 1}/{len(summarized)}): {article['title']}")
        else:
            print(f"          Failed ({idx + 1}/{len(summarized)}): {article['title']}")

    if sent_links:
        updated_seen = seen_links + sent_links
        save_seen(updated_seen)
        print(f"[Done] Saved {len(sent_links)} new link(s) to data/seen.json.")
    else:
        print("[Done] No notifications were sent; data/seen.json was not modified.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
