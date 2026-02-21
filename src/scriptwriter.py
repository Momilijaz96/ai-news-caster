"""Script writer - uses Claude to select top stories and write a briefing script."""

import anthropic
import yaml


def load_config(config_path: str = "config/config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_urdu_prompt(entries: list[dict], config: dict) -> str:
    max_stories = config.get("style", {}).get("max_stories", 8)
    target_minutes = config.get("output", {}).get("target_duration_minutes", 12)
    target_words = int(target_minutes * 130)  # ~130 wpm for Urdu TTS

    entries_text = ""
    for i, entry in enumerate(entries, 1):
        entries_text += f"\n---\n{i}. [{entry['source']}] {entry['title']}\n"
        entries_text += f"   Link: {entry['link']}\n"
        entries_text += f"   Published: {entry['published']}\n"
        entries_text += f"   Summary: {entry['summary']}\n"

    return f"""آپ ایک AI نیوز بریفنگ لکھ رہے ہیں جو آڈیو میں سنائی دے گی — جیسے کوئی دوست صبح چائے پر AI کی تازہ ترین خبریں بتا رہا ہو۔

نیچے دیے گئے news entries میں سے top 5-{max_stories} pick کریں — وہ جو developers اور researchers کے لیے واقعی کام کی ہیں۔ پھر پورا script لکھیں۔

NEWS ENTRIES:
{entries_text}

STRUCTURE (بالکل اسی ترتیب میں):

1. INTRO (2 لائنیں):
   سیدھا شروع کریں۔ کچھ ایسا: "یار، آج [date] ہے — آج AI میں کیا ہو رہا ہے سنو۔" کوئی لمبی greeting نہیں۔

2. ESPRESSO SHOT (30-40 سیکنڈ):
   آج کی top 3 چیزیں ایک ایک لائن میں، بالکل punch کے ساتھ۔ کچھ ایسا:
   "آج تین چیزیں — پہلی: [1 لائن]۔ دوسری: [1 لائن]۔ تیسری: [1 لائن]۔ چلو detail میں چلتے ہیں۔"

3. STORY DETAILS (ہر story کے لیے):
   ہر story کو 2-3 منٹ دیں۔ Transition قدرتی رکھیں جیسے "ٹھیک ہے، اب پہلی والی پر آتے ہیں..." یا "اب دوسری بات..."
   ہر story میں: کیا ہوا، developers/researchers کے لیے کیوں اہم ہے، اپنی honest رائے۔

4. SIGN OFF (1 لائن):
   "بس یار، اتنا تھا آج کا — کل ملتے ہیں۔"

TONE RULES:
- پورا script صحیح اردو رسم الخط میں لکھیں — Roman Urdu نہیں
- Technical terms انگریزی میں رہنے دیں (model, benchmark, API, framework, open source, paper, dataset, fine-tuning, inference, GPU, LLM, agent, prompt, token وغیرہ)
- بالکل casual — کوئی anchoring نہیں، کوئی formal language نہیں
- آراء شامل کریں — "یہ واقعی کافی solid ہے"، "مجھے نہیں لگتا یہ کچھ خاص ہے"، "یہ interesting ہے کیونکہ..."
- چھوٹے چھوٹے جملے، قدرتی وقفے
- کل script تقریباً {target_words} الفاظ کا ہونا چاہیے (~{target_minutes} منٹ at 130 wpm)

FORMATTING:
- کوئی markdown نہیں، کوئی headers نہیں، کوئی bullet points نہیں — یہ spoken script ہے
- کوئی stage directions یا [brackets] نہیں
- پورا script لکھیں، word-for-word، بلند آواز سے پڑھنے کے لیے تیار

اب script لکھیں۔"""


def build_english_summary_prompt(entries: list[dict], config: dict) -> str:
    max_stories = config.get("style", {}).get("max_stories", 8)

    entries_text = ""
    for i, entry in enumerate(entries, 1):
        entries_text += f"\n---\n{i}. [{entry['source']}] {entry['title']}\n"
        entries_text += f"   Link: {entry['link']}\n"
        entries_text += f"   Published: {entry['published']}\n"
        entries_text += f"   Summary: {entry['summary']}\n"

    return f"""Write a short English summary of today's AI news for a WhatsApp message. Pick the top 5-{max_stories} most relevant stories for developers and researchers.

NEWS ENTRIES:
{entries_text}

FORMAT:
- Start with a single intro line (e.g. "Here's your AI news for today:")
- Then one bullet point per story:
  • Story title — one sentence summary. Link: <url>
- End with a short sign-off line (e.g. "That's it for today!")

RULES:
- Plain text only — no markdown, no bold, no asterisks, no headers
- Keep it concise — this is a text message, not an article
- Each bullet point should fit in 2-3 lines max
- Include the link for each story

Write the summary now."""


def write_urdu_script(entries: list[dict], config_path: str = "config/config.yaml") -> str:
    """Use Claude to write a proper Urdu script for TTS audio from aggregated news entries."""
    config = load_config(config_path)
    llm_config = config.get("llm", {})

    client = anthropic.Anthropic()

    prompt = build_urdu_prompt(entries, config)

    print("  Sending to Claude (Urdu script)...")
    message = client.messages.create(
        model=llm_config.get("model", "claude-sonnet-4-20250514"),
        max_tokens=llm_config.get("max_tokens", 4000),
        messages=[{"role": "user", "content": prompt}],
    )

    script = message.content[0].text
    word_count = len(script.split())
    est_minutes = word_count / 130  # Urdu TTS ~130 wpm
    print(f"  Urdu script generated: {word_count} words (~{est_minutes:.1f} min audio)")

    return script


def write_english_summary(entries: list[dict], config_path: str = "config/config.yaml") -> str:
    """Use Claude to write a short English summary suitable for WhatsApp text delivery."""
    config = load_config(config_path)
    llm_config = config.get("llm", {})

    client = anthropic.Anthropic()

    prompt = build_english_summary_prompt(entries, config)

    print("  Sending to Claude (English summary)...")
    message = client.messages.create(
        model=llm_config.get("model", "claude-sonnet-4-20250514"),
        max_tokens=llm_config.get("max_tokens", 4000),
        messages=[{"role": "user", "content": prompt}],
    )

    summary = message.content[0].text
    print(f"  English summary generated: {len(summary.split())} words")

    return summary


def extract_story_list(entries: list[dict], max_stories: int = 8) -> list[dict]:
    """Return top N entries as a structured list for summary generation.

    Each returned dict contains keys: 'title', 'link', 'source'.
    """
    return [
        {"title": e["title"], "link": e["link"], "source": e["source"]}
        for e in entries[:max_stories]
    ]
