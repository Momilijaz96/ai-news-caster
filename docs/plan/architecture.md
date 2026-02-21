# AI News Caster — Architecture

## System Overview

```
Sources (RSS / Twitter / Newsletters)
        ↓
┌─────────────────┐
│   Aggregator    │  Fetch → Filter → Rank
└────────┬────────┘
         ↓
┌─────────────────┐
│  Script Writer  │  LLM → Casual briefing script
└────────┬────────┘
         ↓
┌─────────────────┐
│   TTS Engine    │  Script → MP3 audio
└────────┬────────┘
         ↓
┌─────────────────┐
│    Delivery     │  WhatsApp / Web / Podcast
└─────────────────┘
```

## Module Responsibilities

### `src/aggregator.py`
- Reads source configs from `sources/sources.yaml`
- Fetches RSS feeds via feedparser
- Filters entries: recency (48h), spam keywords
- Boosts entries matching priority keywords
- Sorts by source priority + keyword relevance
- Returns structured list of entries (title, summary, source, link, date)

### `src/scriptwriter.py`
- Takes aggregated entries
- Sends to Claude with prompt for casual briefing style
- Returns plain text script (~10-12 min read-aloud length)
- Config-driven: model, tone, max stories from `config/config.yaml`

### `src/tts.py`
- Takes script text
- Converts via OpenAI TTS API (tts-1-hd, nova voice)
- Handles chunking for scripts >4096 chars
- Concatenates chunks into single MP3
- Config-driven: voice, speed, provider

### `src/main.py`
- Orchestrator: aggregate → script → audio
- Saves all outputs with date stamps
- CLI entry point via `python -m src.main`

## Config Files
- `sources/sources.yaml` — What to aggregate
- `config/config.yaml` — How to process & deliver
- `.env` — API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY)

## Output Files
All date-stamped under their respective directories:
- `scripts/briefing-YYYY-MM-DD.txt`
- `audio/briefing-YYYY-MM-DD.mp3`
- `archive/YYYY-MM-DD.json`
