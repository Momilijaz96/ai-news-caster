# AI News Caster — Raw Requirements

## What It Is
A daily AI news briefing system that aggregates news, generates a concise audio briefing, and delivers it.

## Core Requirements (Agreed)

### Content
- Daily AI news briefing, ~10-12 minutes when read aloud
- Top 5-8 stories per day
- **Tone:** Casual, like catching up with a friend who knows AI
- **Style:** Concise, simple to understand, high-level summaries
- No fluff, no doomscrolling — one coherent briefing replaces scattered reading

### Sources
- RSS feeds: OpenAI Blog, Anthropic News, MIT Tech Review AI, **Latent Space**
- Future: Twitter/X accounts, newsletters (Import AI, The Rundown AI)
- Keyword boosting for: breakthrough, release, launch, open source, safety, regulation
- Filter out: sponsored content, ads, entries older than 48h

### Pipeline
1. **Aggregate** — Pull from RSS feeds, filter & rank by priority/recency
2. **Summarize & Script** — LLM picks top stories, writes casual briefing script
3. **TTS** — Convert script to audio (MP3)
4. **Deliver** — Send to user

### LLM
- Using Claude (Anthropic API) for summarization & script writing
- Open to other models if better options emerge
- Script should feel natural, not robotic

### TTS / Voice
- OpenAI TTS (nova voice) — clean, natural
- Open to ElevenLabs or other options later
- Consistent female voice

### Delivery
- **Schedule:** 10-11 AM Dubai time (GMT+4)
- Briefing stays available until listened to
- **Phase 1:** WhatsApp voice note (personal use)
- **Phase 2:** Transform into a standalone app/product

### Tech Stack
- Python 3
- feedparser for RSS
- anthropic SDK for Claude
- openai SDK for TTS
- pyyaml, python-dotenv
- CLI entry point: `python -m src.main`
- Environment variables for API keys

### Outputs (date-stamped)
- `scripts/briefing-YYYY-MM-DD.txt` — generated script
- `audio/briefing-YYYY-MM-DD.mp3` — audio file
- `archive/YYYY-MM-DD.json` — full metadata + entries

## Vision / Roadmap

### Phase 1 — Personal Tool
- Get pipeline working end-to-end
- Daily cron job for morning delivery
- WhatsApp voice note delivery via Clawdbot

### Phase 2 — Better Content
- More sources (Twitter/X, newsletters, HuggingFace blog)
- Better story ranking & deduplication
- Tune script tone & length
- Editorial review option (preview script before audio)

### Phase 3 — Product / App
- Web player UI
- Podcast RSS feed generation
- Mobile app
- Multi-user support
- Custom topic preferences
- User onboarding

## Non-Functional
- Production-quality but simple — no over-engineering
- Modular architecture (swap sources, LLM, TTS, delivery independently)
- Build clean enough to productize later
