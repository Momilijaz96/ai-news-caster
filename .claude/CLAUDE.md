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
3. **TTS** — OpenAI TTS (nova voice) → MP3
4. **Deliver** — WhatsApp voice note (phase 1), standalone app (phase 2)

### Delivery
- Schedule: 10-11 AM Dubai time (GMT+4)
- Stays available until listened to

### Tech Stack
- Python 3, feedparser, anthropic SDK, openai SDK, pyyaml, python-dotenv
- CLI: `python -m src.main`
- Env vars: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`

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
   TTS Engine (OpenAI nova → MP3)
        ↓
   Delivery (WhatsApp / Web / Podcast)
```

### Modules
- `src/aggregator.py` — RSS fetching, filtering, ranking
- `src/scriptwriter.py` — Claude-powered script generation
- `src/tts.py` — OpenAI TTS, chunking for long scripts
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
- Claude for summarization, OpenAI for TTS
- Modular — each step swappable independently
- Build for personal use first, productize later
