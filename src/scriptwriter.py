"""Script writer - uses Claude to select top stories and write a briefing script."""

import anthropic
import yaml


def load_config(config_path: str = "config/config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_prompt(entries: list[dict], config: dict) -> str:
    max_stories = config.get("style", {}).get("max_stories", 8)
    target_minutes = config.get("output", {}).get("target_duration_minutes", 12)

    entries_text = ""
    for i, entry in enumerate(entries, 1):
        entries_text += f"\n---\n{i}. [{entry['source']}] {entry['title']}\n"
        entries_text += f"   Link: {entry['link']}\n"
        entries_text += f"   Published: {entry['published']}\n"
        entries_text += f"   Summary: {entry['summary']}\n"

    return f"""You're writing a daily AI news audio briefing — like a knowledgeable friend casually catching you up over coffee.

Pick the top 5-{max_stories} stories from the entries below that are most relevant to developers and researchers. Then write the full script.

NEWS ENTRIES:
{entries_text}

STRUCTURE (in this exact order):

1. INTRO (1-2 lines):
   Jump straight in. Something like: "Hey, it's [date] — here's what's happening in AI today." No lengthy intros.

2. ESPRESSO SHOT (30-40 seconds):
   Top 3 stories in one punchy line each. Like:
   "Three things today — first: [1 line]. Second: [1 line]. Third: [1 line]. Let's get into it."

3. STORY DETAILS (per story):
   2-3 minutes per story. Natural transitions like "Alright, starting with..." or "Next up..."
   For each: what happened, why it matters for developers/researchers, your honest take.

4. SIGN OFF (1 line):
   "That's it for today — catch you tomorrow."

TONE:
- Casual and direct — like a smart friend, not a news anchor
- Short sentences, natural rhythm
- Include opinions — "this is actually pretty solid", "I'm not sure this changes much", "interesting because..."
- No fluff, no filler

FORMATTING:
- No markdown, no headers, no bullet points — this is a spoken script
- No stage directions or [brackets]
- Write the full script, word-for-word, ready to read aloud
- Target: ~{target_minutes * 150} words (~{target_minutes} min at 150 wpm)

Write the script now."""


def write_script(entries: list[dict], config_path: str = "config/config.yaml") -> str:
    """Use Claude to write a casual English briefing script from aggregated news entries."""
    config = load_config(config_path)
    llm_config = config.get("llm", {})

    client = anthropic.Anthropic()
    prompt = build_prompt(entries, config)

    print("  Sending to Claude...")
    message = client.messages.create(
        model=llm_config.get("model", "claude-sonnet-4-20250514"),
        max_tokens=llm_config.get("max_tokens", 4000),
        messages=[{"role": "user", "content": prompt}],
    )

    script = message.content[0].text
    word_count = len(script.split())
    est_minutes = word_count / 150
    print(f"  Script generated: {word_count} words (~{est_minutes:.1f} min read time)")

    return script


def extract_story_list(entries: list[dict], max_stories: int = 8) -> list[dict]:
    """Return top N entries as a structured list for summary generation.

    Each returned dict contains keys: 'title', 'link', 'source'.
    """
    return [
        {"title": e["title"], "link": e["link"], "source": e["source"]}
        for e in entries[:max_stories]
    ]
