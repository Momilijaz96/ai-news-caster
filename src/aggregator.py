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
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        })
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")

        # Slugs appear as href="/owner/repo" data-view-component="true" — ordered list of repos
        slugs = re.findall(
            r'href="/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"\s*data-view-component="true"', html
        )
        # Stars today — in same order as repos
        stars_list = re.findall(r'([\d,]+)\s*stars today', html)

        # Keywords that must appear as whole words/phrases (word-boundary matched)
        # to avoid false positives like "wagtail" matching "ai", "dragonfly" matching "rag"
        ai_keywords_whole = [
            r"\bai\b", r"\bllm\b", r"\bgpt\b", r"\bml\b", r"\bneural\b",
            r"\bdiffusion\b", r"\btransformer\b", r"\bembedding\b", r"\brag\b",
            r"\binference\b", r"\blangchain\b", r"\bopenai\b", r"\bclaude\b",
            r"\bmistral\b", r"\bllama\b", r"\bgemini\b", r"\bmultimodal\b",
            r"\bcopilot\b", r"\bhuggingface\b", r"\bpytorch\b", r"\btensorflow\b",
            r"\bnlp\b", r"\bautonomous\b", r"\bdeep.learning\b",
            r"\bmachine.learning\b", r"\bcomputer.vision\b",
            r"\bagent\b", r"\bchatgpt\b", r"\bstable.diffusion\b",
        ]
        # Substring keywords (safe — unlikely to appear in non-AI repo names)
        ai_keywords_sub = ["fine-tun", "vector store", "language model"]

        def _is_ai_repo(text: str) -> bool:
            for pattern in ai_keywords_whole:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            for kw in ai_keywords_sub:
                if kw in text:
                    return True
            return False

        count = 0
        for i, slug in enumerate(slugs):
            if count >= max_repos:
                break

            stars = stars_list[i] if i < len(stars_list) else "?"

            # Extract description from the HTML section near this slug
            # Description appears as a long text node (>30 chars) in the slug's area
            idx = html.find(f'/{slug}"')
            if idx < 0:
                continue
            # Look in a ~3KB window after the slug reference
            window = html[idx:idx + 3000]
            # Get plain text chunks — skip SVG/HTML noise
            text_chunks = re.findall(r'>\s*([^<]{30,}?)\s*<', window)
            # First long text chunk is typically the repo description
            desc = text_chunks[0].strip() if text_chunks else ""
            # Clean whitespace
            desc = re.sub(r'\s+', ' ', desc)

            combined = f"{slug} {desc}"
            if _is_ai_repo(combined):
                entries.append({
                    "title": f"🔥 Trending on GitHub: {slug} ({stars} stars today)",
                    "link": f"https://github.com/{slug}",
                    "summary": desc[:500] if desc else f"Trending AI/ML repo: {slug}",
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
        # Per-feed hours_back override (e.g. weekly newsletters use 168h)
        feed_hours_back = feed_config.get("hours_back", hours_back)
        entries = fetch_feed(feed_config, feed_hours_back)
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
