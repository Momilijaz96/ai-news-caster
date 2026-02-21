"""RSS feed aggregator - fetches and ranks AI news from configured sources."""

import feedparser
import yaml
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_sources(sources_path: str = "sources/sources.yaml") -> dict:
    with open(sources_path) as f:
        return yaml.safe_load(f)


def fetch_feed(feed_config: dict, hours_back: int = 48) -> list[dict]:
    """Fetch recent entries from a single RSS feed."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    entries = []

    try:
        feed = feedparser.parse(feed_config["url"])
        for entry in feed.entries:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            # If no date, include it (might be recent)
            if published and published < cutoff:
                continue

            entries.append({
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:500],
                "published": published.isoformat() if published else "unknown",
                "source": feed_config["name"],
                "priority": feed_config.get("priority", "medium"),
            })
    except Exception as e:
        print(f"  Warning: Failed to fetch {feed_config['name']}: {e}")

    return entries


def aggregate(sources_path: str = "sources/sources.yaml", hours_back: int = 48) -> list[dict]:
    """Fetch all RSS feeds and return combined entries sorted by priority/recency."""
    sources = load_sources(sources_path)
    all_entries = []

    for feed_config in sources.get("rss_feeds", []):
        print(f"  Fetching: {feed_config['name']}...")
        entries = fetch_feed(feed_config, hours_back)
        all_entries.extend(entries)
        print(f"    Found {len(entries)} recent entries")

    # Sort: high priority first, then by date
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_entries.sort(key=lambda x: (
        priority_order.get(x["priority"], 1),
        x["published"] == "unknown",
    ))

    # Load boost/skip keywords for basic filtering
    keywords_skip = sources.get("keywords_skip", [])
    filtered = []
    for entry in all_entries:
        text = f"{entry['title']} {entry['summary']}".lower()
        if any(kw.lower() in text for kw in keywords_skip):
            continue
        filtered.append(entry)

    print(f"  Total: {len(filtered)} entries after filtering")
    return filtered
