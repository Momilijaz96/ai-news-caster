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

    return f"""Tu ek AI news briefing likh raha hai jo audio mein sunai degi — jaise koi dost subah chai pe AI ki latest cheezein bata raha ho.

Neeche diye gaye news entries mein se top 5-{max_stories} pick kar — woh jo actual mein kaam ki hain developers aur researchers ke liye. Phir poora script likh.

NEWS ENTRIES:
{entries_text}

STRUCTURE (bilkul isi order mein):

1. INTRO (2 lines):
   Seedha shuru ho. Kuch aisa: "Yaar, [date] hai — aaj AI mein kya ho raha hai sunlo." Koi lengthy greeting nahi.

2. ESPRESSO SHOT (30-40 seconds):
   Aaj ki top 3 cheezein ek ek line mein, ekdum punch ke saath. Kuch aisa:
   "Aaj teen cheezein — pehli: [1 line]. Doosri: [1 line]. Teesri: [1 line]. Chalo detail mein chalte hain."

3. STORY DETAILS (har story ke liye):
   Har story ko 2-3 minute do. Transition natural rakho jaise "Theek hai, ab pehli wali pe aate hain..." ya "Ab doosri baat..."
   Har story mein: kya hua, kyun matter karta hai developer/researcher ke liye, teri apni honest rai.

4. SIGN OFF (1 line):
   "Bas yaar, itna tha aaj ka — kal milte hain."

TONE RULES:
- Roman Urdu mein likh — jaise Pakistani log actually bolte hain. Technical terms English mein rehne do (model, benchmark, API, framework, open source, paper, etc.)
- Bilkul casual — koi anchoring nahi, koi formal language nahi
- Opinions daal — "yeh actually kafi solid hai", "mujhe nahi lagta yeh kuch khas hai", "yeh interesting hai kyunki..."
- Chhote chhote sentences, natural pauses
- Total script {target_minutes} minutes ka hona chahiye (~{target_minutes * 150} words at 150 wpm)

FORMATTING:
- Koi markdown nahi, koi headers nahi, koi bullet points nahi — yeh spoken script hai
- Koi stage directions ya [brackets] nahi
- Poora script likh, word-for-word ready to read aloud

Ab script likh."""


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
