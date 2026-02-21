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

    return f"""You are writing a daily AI news briefing script that will be read aloud as a podcast/audio briefing.

FROM THE FOLLOWING NEWS ENTRIES, pick the top 5-{max_stories} most important, interesting, or impactful stories. Then write a complete briefing script.

NEWS ENTRIES:
{entries_text}

REQUIREMENTS:
- Pick 5-{max_stories} stories. Prioritize: major releases, breakthroughs, safety/regulation news, open source launches.
- Write a script that takes about {target_minutes} minutes to read aloud (~150 words per minute, so ~{target_minutes * 150} words).
- Tone: casual, like you're catching up with a smart friend over coffee. Concise and simple - no jargon dumps.
- Include a brief intro/greeting and a sign-off.
- For each story: explain what happened, why it matters, keep it high-level.
- Transition naturally between stories.
- Do NOT use markdown, headers, bullet points, or any formatting. This is a spoken script - write it as natural speech.
- Do NOT include stage directions, sound cues, or [brackets].
- Write the COMPLETE script, ready to be read aloud word-for-word.

Write the script now."""


def write_script(entries: list[dict], config_path: str = "config/config.yaml") -> str:
    """Use Claude to write a briefing script from aggregated news entries."""
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
