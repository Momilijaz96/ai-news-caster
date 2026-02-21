# CLAUDE.md — AI News Caster

## What It Is
Daily AI news audio briefing system. Aggregates news → LLM writes casual script → TTS generates audio → delivers via WhatsApp.

## Requirements

### Content
- Daily briefing, ~10-12 min read-aloud, top 5-8 stories
- **Tone:** Casual, like catching up with a friend who knows AI
- **Style:** Concise, simple, high-level. No fluff.

### Sources
- RSS: OpenAI Blog, Anthropic News, MIT Tech Review AI, Latent Space
- Future: Twitter/X, newsletters (Import AI, The Rundown AI)
- Keyword boost: breakthrough, release, launch, open source, safety, regulation
- Filter: sponsored, ads, entries >48h old

### Pipeline
1. **Aggregate** — Fetch RSS → filter & rank by priority/recency
2. **Script** — Claude picks top stories → writes casual briefing script
3. **TTS** — Edge TTS (free, unlimited, no API key) → MP3
4. **Deliver** — WhatsApp voice note (phase 1), standalone app (phase 2)

### Delivery
- Schedule: 10-11 AM Dubai time (GMT+4)
- Stays available until listened to

### TTS / Voice
- **Use `edge-tts` Python package** — free, unlimited, no API key needed
- Voice: `en-US-JennyNeural` or `en-US-AriaNeural` (natural female, NO robotic/accented)
- Python: `import edge_tts; communicate = edge_tts.Communicate(text, "en-US-JennyNeural"); await communicate.save("output.mp3")`
- Replace OpenAI TTS entirely with edge-tts
- Add `edge-tts` to requirements.txt

### Tech Stack
- Python 3, feedparser, anthropic SDK, edge-tts, pyyaml, python-dotenv
- CLI: `python -m src.main`
- Env vars: `ANTHROPIC_API_KEY`

### Outputs (date-stamped)
- `scripts/briefing-YYYY-MM-DD.txt`
- `audio/briefing-YYYY-MM-DD.mp3`
- `archive/YYYY-MM-DD.json`

## Architecture

```
Sources (RSS / Twitter / Newsletters)
        ↓
   Aggregator (fetch → filter → rank)
        ↓
   Script Writer (Claude LLM → casual script)
        ↓
   TTS Engine (Edge TTS, en-US-JennyNeural → MP3)
        ↓
   Delivery (WhatsApp / Web / Podcast)
```

### Modules
- `src/aggregator.py` — RSS fetching, filtering, ranking
- `src/scriptwriter.py` — Claude-powered script generation
- `src/tts.py` — Edge TTS (edge-tts package), async, no API key needed
- `src/main.py` — Pipeline orchestrator
- `sources/sources.yaml` — Source configs
- `config/config.yaml` — App settings

## Current State (v0.1)
Core pipeline built and functional. Needs API keys in `.env` to run.

```bash
cp .env.example .env  # Add API keys
pip install -r requirements.txt
python -m src.main
```

## WhatsApp Delivery (LOCAL ONLY)
WhatsApp delivery runs **locally on the host machine** via the `openclaw` CLI.
It connects through a local WhatsApp gateway — it CANNOT run on GitHub Actions or any remote CI.

**There is no `WHATSAPP_SESSION` secret.** The session is managed by the local OpenClaw gateway daemon.

```bash
openclaw message send --channel whatsapp \
  --target "$WHATSAPP_TARGET_NUMBER" \
  --media <path-to-audio.mp3> \
  --message "🎙️ Your AI briefing is ready"
```

In Python:
```python
import subprocess
import os

def deliver_whatsapp(audio_path):
    target = os.getenv("WHATSAPP_TARGET_NUMBER", "+923479075154")
    subprocess.run([
        "openclaw", "message", "send",
        "--channel", "whatsapp",
        "--target", target,
        "--media", audio_path,
        "--message", "🎙️ Your AI briefing is ready"
    ], check=True)
```

**Important:** If building a GitHub Actions workflow, separate concerns:
- GH Actions: aggregate + script + TTS → generate audio artifact
- Local cron: download artifact → deliver via openclaw
Or just run the entire pipeline locally via cron (simpler for v1).

## TODO
### Phase 1 — Daily Delivery
- [ ] Test end-to-end run
- [ ] Cron job for 10-11 AM Dubai time
- [ ] WhatsApp delivery via Clawdbot

### Phase 2 — Better Content
- [ ] More sources (HuggingFace, Twitter/X, newsletters)
- [ ] Story ranking & dedup
- [ ] Tune script tone & length

### Phase 3 — Product
- [ ] Web player UI
- [ ] Podcast RSS feed
- [ ] Mobile app
- [ ] Multi-user + custom preferences

## Key Decisions
- Python 3, keep it simple
- Claude for summarization, Edge TTS for voice (free, no API key)
- Modular — each step swappable independently
- Build for personal use first, productize later
