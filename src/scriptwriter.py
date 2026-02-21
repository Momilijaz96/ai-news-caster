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

    from datetime import datetime
    import zoneinfo
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Dubai"))
    today = now.strftime("%A, %B %-d")  # e.g. "Sunday, February 22"

    return f"""You are the host of a friendly morning AI news briefing — think Morning Brew but for developers. Casual, warm, smart. Easy to absorb with your first coffee.

Pick the 3 best stories from the entries below. Best = actually buzzing right now. Things developers are sharing, debating, excited or freaked out about.

TODAY'S DATE: {today}

NEWS ENTRIES:
{_entries_text(entries, max_stories)}

STRUCTURE — follow this exactly:

1. OPENER — GREETING + STAKES + RAPID TEASE (3 sentences MAX)
   Sentence 1: Warm, punchy hello — address the listener by name: Momal. Like a friend who's excited to catch up.
   Sentence 2: Set the energy — bold claim or mood-setter about what's going on in AI today.
   Sentence 3: Rapid-fire all 3 story names back-to-back — just the titles, no details, make them curious.
   Example: "Hey Momal, happy Sunday morning! The AI world did not sleep this weekend. We've got llama.cpp getting acquired, a viral tool to block AI slop, and a wild AI agent drama."
   Then add a DIVE-IN LINE — one punchy sentence that transitions into the stories.
   Example: "Alright, let's get into it." or "Here's what you need to know." or "Let's break it down."

2. STORY RUNDOWN — for each of the 3 stories:
   a) HOOK LINE (1 sentence — the punchy headline drop)
      The most surprising/intriguing fact. Short. Declarative. Let it hang.
   b) [pause] — write this literally, on its own line
   c) THE UNPACK (2-3 sentences)
      Now breathe and explain. Why it matters + honest hot take. Like telling a friend.
   d) PUNCHLINE / CONNECTOR (1 sentence)
      Land it with your reaction OR bridge to the next story with energy.
      Examples: "This one's going to keep getting bigger." / "And speaking of things developers can't stop talking about..." / "Wild, right? But wait, it gets weirder."
   e) [pause] — write this literally, signals the beat before next story

3. SIGN OFF (1-2 sentences)
   Confident and warm — like a host who'll be back tomorrow.
   Example: "That's your AI fix for {today}. Links and full details below — see you tomorrow."

TONE:
- Think: Howard Stern's confidence + Morning Brew's warmth + Bill Simmons' buddy energy
- Short sentences. Punchy. Room to breathe.
- Real reactions — don't be neutral, have an actual opinion
- Speak TO the listener, not AT them

AVOID:
- "Furthermore", "it's worth noting", "interestingly"
- "Game-changing", "revolutionary", "unprecedented"
- Soft openers like "So today we have..." or "Let's start with..."
- Thesis wrap-ups — just sign off

FORMATTING:
- PLAIN TEXT ONLY. No asterisks, no bold, no markdown of any kind. This is spoken audio.
- Target: ~280-320 words (~2 min at 130 wpm) — tight and punchy

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
