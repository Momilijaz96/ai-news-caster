"""Script writer - uses Claude to write audio teaser and WhatsApp detail summary."""

import anthropic
import yaml


def load_config(config_path: str = "config/config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _entries_text(entries: list[dict], max_stories: int) -> str:
    text = ""
    for i, entry in enumerate(entries[:max_stories * 2], 1):  # give Claude more to pick from
        text += f"\n---\n{i}. [{entry['source']}] {entry['title']}\n"
        text += f"   Link: {entry['link']}\n"
        text += f"   Summary: {entry['summary']}\n"
    return text


def build_audio_prompt(entries: list[dict], config: dict) -> str:
    max_stories = config.get("style", {}).get("max_stories", 8)

    return f"""You're writing a punchy 3-5 minute audio teaser for a daily AI news briefing.

Think of it like a movie trailer for today's AI news — hook the listener, tease the highlights, make them curious. NOT a full explainer.

Pick the top 5 most interesting stories from the entries below. Then write the spoken audio script.

NEWS ENTRIES:
{_entries_text(entries, max_stories)}

STRUCTURE:

1. COLD OPEN (1-2 sentences):
   Start with the single most interesting thing happening today. No intro, no "hey welcome back" — just drop straight into the news like a hook.
   Example: "Someone just open-sourced a model that's giving GPT-4 a run for its money. That's the headline today."

2. THE HIGHLIGHTS (one punchy line per story, 5 stories):
   Rapid-fire. Each story gets ONE sentence — just enough to intrigue, not explain.
   No transitions needed, just boom boom boom.

3. SIGN OFF (1 line):
   "Full details and links in the description — catch you tomorrow."

TONE:
- Energetic, punchy, like a sports highlight reel not a lecture
- Short sentences. Fragments are fine. Punch > completeness.
- Opinions welcome — "this one's big", "honestly not sure it matters yet", "this changes things"
- NO explaining, NO deep dives — save that for the WhatsApp text

FORMATTING:
- No markdown, no headers, no bullet points — spoken script only
- No stage directions or [brackets]
- Target: ~500-600 words MAX (~3-4 min at 150 wpm)

Write the script now."""


def build_whatsapp_prompt(entries: list[dict], config: dict) -> str:
    max_stories = config.get("style", {}).get("max_stories", 8)

    return f"""Write a detailed WhatsApp message summarizing today's top AI news stories for a developer/researcher audience.

This is the "full details" companion to a short audio teaser — readers want substance here.

Pick the top 5 stories from the entries below.

NEWS ENTRIES:
{_entries_text(entries, max_stories)}

FORMAT — write it exactly like this:

🎙️ Today's AI Briefing — [Date]

1. [Story Title]
[2-3 sentences: what happened + why it matters to developers/researchers]
🔗 [link]

2. [Story Title]
[2-3 sentences]
🔗 [link]

(repeat for all 5 stories)

---
Full audio briefing above ☝️

RULES:
- Plain text only — no bold, no asterisks, no markdown
- Keep each story to 2-3 sentences max — tight and useful
- Lead with what matters, not background context
- Include the link for every story

Write it now."""


def write_script(entries: list[dict], config_path: str = "config/config.yaml") -> str:
    """Write a punchy 3-5 min audio teaser script."""
    config = load_config(config_path)
    llm_config = config.get("llm", {})

    client = anthropic.Anthropic()
    prompt = build_audio_prompt(entries, config)

    print("  Sending to Claude (audio teaser)...")
    message = client.messages.create(
        model=llm_config.get("model", "claude-sonnet-4-20250514"),
        max_tokens=llm_config.get("max_tokens", 4000),
        messages=[{"role": "user", "content": prompt}],
    )

    script = message.content[0].text
    word_count = len(script.split())
    est_minutes = word_count / 150
    print(f"  Audio script: {word_count} words (~{est_minutes:.1f} min)")
    return script


def write_whatsapp_summary(entries: list[dict], config_path: str = "config/config.yaml") -> str:
    """Write a detailed WhatsApp text summary with full story details and links."""
    config = load_config(config_path)
    llm_config = config.get("llm", {})

    client = anthropic.Anthropic()
    prompt = build_whatsapp_prompt(entries, config)

    print("  Sending to Claude (WhatsApp summary)...")
    message = client.messages.create(
        model=llm_config.get("model", "claude-sonnet-4-20250514"),
        max_tokens=llm_config.get("max_tokens", 4000),
        messages=[{"role": "user", "content": prompt}],
    )

    summary = message.content[0].text
    print(f"  WhatsApp summary: {len(summary.split())} words")
    return summary


def extract_story_list(entries: list[dict], max_stories: int = 8) -> list[dict]:
    """Return top N entries as a structured list for archive."""
    return [
        {"title": e["title"], "link": e["link"], "source": e["source"]}
        for e in entries[:max_stories]
    ]
