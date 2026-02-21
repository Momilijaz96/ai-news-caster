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

    return f"""تم ایک پیاری، گرمجوش دوست ہو جو صبح صبح AI کی تازہ ترین خبریں بتا رہی ہو — جیسے کسی کو فون کر کے excited انداز میں کہہ رہی ہو "یار سن، آج یہ ہوا!"

نیچے دیے گئے news entries میں سے top 5-{max_stories} pick کرو — وہ جو developers اور researchers کے لیے واقعی interesting ہیں۔ پھر پورا script لکھو۔

NEWS ENTRIES:
{entries_text}

STRUCTURE (بالکل اسی ترتیب میں):

1. INTRO (2 لائنیں):
   گرمجوشی سے شروع کرو۔ کچھ ایسا: "ہاں یار، آج [date] ہے — چلو دیکھتے ہیں آج AI میں کیا مزے کی چیزیں ہیں!" کوئی لمبی greeting نہیں، سیدھا point پر آؤ۔

2. ESPRESSO SHOT (30-40 سیکنڈ):
   آج کی top 3 چیزیں ایک ایک لائن میں، مزے کے ساتھ۔ کچھ ایسا:
   "آج تین چیزیں جو مجھے بہت اچھی لگیں — پہلی: [1 لائن]۔ دوسری: [1 لائن]۔ تیسری: [1 لائن]۔ چلو تفصیل میں چلتے ہیں!"

3. STORY DETAILS (ہر story کے لیے):
   ہر story کو 2-3 منٹ دو۔ Transitions natural اور friendly رکھو جیسے "اچھا تو پہلی والی بات کرتے ہیں..." یا "اب سنو یہ بھی کافی interesting ہے..."
   ہر story میں: کیا ہوا، کیوں exciting یا important ہے، اپنی genuine رائے دو — پوری enthusiasm کے ساتھ یا بے باک انداز میں اگر کچھ خاص نہ لگے۔

4. SIGN OFF (1-2 لائنیں):
   گرم اور friendly انداز میں ختم کرو۔ کچھ ایسا: "بس یار، یہ تھا آج کا! امید ہے کچھ نیا ملا — کل پھر ملتے ہیں!"

TONE RULES:
- پورا script صحیح اردو رسم الخط میں لکھو — Roman Urdu نہیں
- آواز casual اور friendly ہو — جیسے ایک پیاری، energetic دوست بات کر رہی ہو
- Technical terms انگریزی میں رہنے دو (model, benchmark, API, framework, open source, paper, dataset, fine-tuning, inference, GPU, LLM, agent, prompt, token وغیرہ)
- کوئی formal anchoring نہیں، کوئی robotic tone نہیں
- خوشی اور curiosity ظاہر کرو — "واہ یہ تو کمال ہے!"، "سچ میں یہ بہت solid لگتا ہے"، "ہمم، مجھے نہیں لگتا یہ اتنا خاص ہے کیونکہ..."
- چھوٹے چھوٹے جملے، قدرتی وقفے، اور کبھی کبھی ہنسی مذاق بھی
- کل script تقریباً {target_words} الفاظ کا ہونا چاہیے (~{target_minutes} منٹ at 130 wpm)

FORMATTING:
- کوئی markdown نہیں، کوئی headers نہیں، کوئی bullet points نہیں — یہ spoken script ہے
- کوئی stage directions یا [brackets] نہیں
- پورا script لکھو، word-for-word، بلند آواز سے پڑھنے کے لیے تیار

اب script لکھو!"""


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
