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

    return f"""You're a senior ML engineer writing a 3-minute spoken audio briefing for fellow developers.

Your job: pick the 3 stories that are actually causing a stir right now. Things people are sharing, debating, or excited about. Trending GitHub repos, viral model releases, hot HN threads, things that make developers stop and go "wait, what?"

Skip anything boring, incremental, or corporate PR. If a story wouldn't make a developer stop scrolling, don't pick it.

NEWS ENTRIES:
{_entries_text(entries, max_stories)}

STRUCTURE:

1. GREETING (1-2 sentences):
   Warm, casual welcome. Like texting a friend. Use the date naturally.
   Example: "Hey! Happy Sunday — hope you're having a good one. Got some spicy AI news for you today."
   Or: "Good morning! It's [day], and the AI world did not take the weekend off."

2. THREE STORIES:
   For each story — exactly 3 sentences:
   - What happened (1 sentence, concrete and specific)
   - Why developers should care (1 sentence)
   - Your honest reaction (1 sentence — excited, skeptical, impressed, whatever's real)

3. SIGN OFF (1 line):
   "Full details and links in the text below — see you tomorrow."

TONE:
- Write for ears, not eyes — slow pace, short sentences, space to breathe
- Sound like a developer talking to a developer — no hype, no buzzwords, real takes
- One idea per sentence. Full stop. Move on.
- Be specific — "a 70B model that beats GPT-4 on coding" not "a powerful new model"

AVOID:
- Filler words: "furthermore", "it's worth noting", "interestingly"
- Vague claims: "game-changing", "revolutionary", "unprecedented"
- Cramming details — the WhatsApp text has the details

FORMATTING:
- Plain text only, no markdown
- Target: ~400 words (~3 min at 130 wpm)

Write the script now."""


def build_whatsapp_prompt(entries: list[dict], config: dict) -> str:
    max_stories = config.get("style", {}).get("max_stories", 8)

    return f"""Write a detailed WhatsApp message summarizing today's top AI news stories for a developer/researcher audience.

This is the "full details" companion to a short audio teaser — readers want substance here.

Pick the top 5 most interesting/trending stories from the entries below. Prioritize things that are actually causing buzz — viral repos, hot model releases, trending HN threads — over dry corporate announcements.

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
