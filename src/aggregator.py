"""RSS feed aggregator - fetches and ranks AI news from configured sources."""

import re
import urllib.request
import feedparser
import yaml
from datetime import datetime, timedelta, timezone


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


def fetch_github_trending(max_repos: int = 10) -> list[dict]:
    """Scrape GitHub Trending for top AI/ML repos today."""
    entries = []
    try:
        url = "https://github.com/trending?since=daily&spoken_language_code=en"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")

        # Extract repo blocks: owner/name + description + stars
        # Extract repo slugs
        slugs = re.findall(r'href="/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"', html)
        # Extract descriptions
        descs = re.findall(r'<p\s+class="col-9[^"]*">\s*(.*?)\s*</p>', html, re.DOTALL)
        # Extract stars today
        stars_today = re.findall(r'([\d,]+)\s*stars today', html)

        repos = list(zip(slugs, descs + [''] * len(slugs), stars_today + ['?'] * len(slugs)))

        ai_keywords = {"ai", "llm", "gpt", "ml", "model", "agent", "neural",
                       "diffusion", "transformer", "embedding", "rag", "vector",
                       "inference", "fine-tun", "langchain", "openai", "claude",
                       "mistral", "llama", "gemini", "vision", "multimodal"}

        count = 0
        for slug, desc, stars in repos:
            if count >= max_repos:
                break
            combined = f"{slug} {desc}".lower()
            if any(kw in combined for kw in ai_keywords):
                clean_desc = re.sub(r'\s+', ' ', desc.strip())
                entries.append({
                    "title": f"🔥 Trending on GitHub: {slug} ({stars} stars today)",
                    "link": f"https://github.com/{slug}",
                    "summary": clean_desc[:500] if clean_desc else f"Trending AI/ML repo: {slug}",
                    "published": datetime.now(timezone.utc).isoformat(),
                    "source": "GitHub Trending",
                    "priority": "high",
                })
                count += 1

    except Exception as e:
        print(f"  Warning: GitHub Trending fetch failed: {e}")

    return entries


def aggregate(sources_path: str = "sources/sources.yaml", hours_back: int = 48) -> list[dict]:
    """Fetch all sources and return combined entries sorted by priority/recency."""
    sources = load_sources(sources_path)
    all_entries = []

    # RSS feeds
    for feed_config in sources.get("rss_feeds", []):
        print(f"  Fetching: {feed_config['name']}...")
        entries = fetch_feed(feed_config, hours_back)
        all_entries.extend(entries)
        print(f"    Found {len(entries)} recent entries")

    # GitHub Trending
    print(f"  Fetching: GitHub Trending...")
    gh_entries = fetch_github_trending()
    all_entries.extend(gh_entries)
    print(f"    Found {len(gh_entries)} trending AI repos")

    # Sort: high priority first, then recency
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_entries.sort(key=lambda x: (
        priority_order.get(x["priority"], 1),
        x["published"] == "unknown",
    ))

    # Skip filtered keywords
    keywords_skip = sources.get("keywords_skip", [])
    filtered = []
    for entry in all_entries:
        text = f"{entry['title']} {entry['summary']}".lower()
        if any(kw.lower() in text for kw in keywords_skip):
            continue
        filtered.append(entry)

    print(f"  Total: {len(filtered)} entries after filtering")
    return filtered
