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

    return f"""You're writing a 3-minute spoken audio briefing. It will be listened to, not read.

Pick the top 3 stories from the entries below. Just 3 — quality over quantity.

NEWS ENTRIES:
{_entries_text(entries, max_stories)}

STRUCTURE:

1. COLD OPEN (1 sentence):
   The single most interesting thing today. Drop straight in. No greeting.
   Example: "Someone just open-sourced a model that's giving GPT-4 a run for its money."

2. THREE STORIES (one per story):
   For each story:
   - One sentence: what happened
   - One sentence: why it's interesting
   - One sentence: your honest take
   That's it. 3 sentences per story. Hard limit.

3. SIGN OFF (1 line):
   "Details and links are in the text below — see you tomorrow."

TONE:
- Slow down. Leave space. This is audio, not text.
- Write how you'd actually say it out loud to a friend — not how you'd write it
- Short sentences. One idea per sentence. Full stop. New thought.
- Conversational opinions — "this is actually big", "not sure it matters yet", "keep an eye on this one"

WHAT TO AVOID:
- No "furthermore", "additionally", "it's worth noting" — cut all filler
- No lists, no "first... second... third..."
- No more than 10 words per sentence ideally
- Don't cram in details — details live in the WhatsApp text

FORMATTING:
- Plain text, no markdown, no headers
- Target: ~400 words (~3 min at 130 wpm — spoken pace is slower than reading)

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
