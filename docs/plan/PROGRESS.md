# AI News Caster — Progress & Plan

## ✅ Completed (v0.1 — Feb 21, 2026)

### Pipeline Built
| File | Purpose |
|------|---------|
| `src/aggregator.py` | Fetches RSS feeds, filters by recency (48h) and keywords, sorts by priority |
| `src/scriptwriter.py` | Sends aggregated entries to Claude, gets back a casual briefing script |
| `src/tts.py` | Converts script to MP3 via OpenAI TTS (nova voice), handles chunking for long scripts |
| `src/main.py` | Orchestrates the 3-step pipeline, saves date-stamped outputs |
| `src/__main__.py` | Enables `python -m src` |
| `requirements.txt` | Dependencies |
| `.env.example` | API key template |
| `sources/sources.yaml` | RSS feed configs |
| `config/config.yaml` | App settings |

### Pipeline Flow
1. **Aggregate** — Fetch RSS feeds → filter old entries (>48h) + spam keywords → sort by priority
2. **Script** — Send entries to Claude → get ~10-12 min casual briefing script
3. **Audio** — Send script to OpenAI TTS (tts-1-hd, nova voice) → split chunks if >4096 chars → save MP3

### Outputs (date-stamped)
- `scripts/briefing-YYYY-MM-DD.txt`
- `audio/briefing-YYYY-MM-DD.mp3`
- `archive/YYYY-MM-DD.json`

## 🔧 To Run
```bash
cp .env.example .env   # Add ANTHROPIC_API_KEY and OPENAI_API_KEY
pip install -r requirements.txt
python -m src.main
```

## 📋 TODO (Next Steps)

### Phase 1 — Get It Running Daily
- [ ] Add API keys to .env
- [ ] Test end-to-end run
- [ ] Set up cron job for 10-11 AM Dubai time delivery
- [ ] WhatsApp delivery integration (send audio via Clawdbot)

### Phase 2 — Improve Content
- [ ] Add more RSS sources (Latent Space, HuggingFace blog, etc.)
- [ ] Twitter/X integration for breaking news
- [ ] Newsletter parsing (Import AI, The Rundown)
- [ ] Better story ranking/dedup
- [ ] Tune the script tone & length

### Phase 3 — Product-ify
- [ ] Web player UI
- [ ] Podcast RSS feed generation
- [ ] Mobile app (React Native?)
- [ ] Multi-user support
- [ ] Custom topic preferences

## Architecture
```
sources (RSS/Twitter/newsletters)
        ↓
   Aggregator (fetch + filter + rank)
        ↓
   Script Writer (Claude LLM → casual briefing)
        ↓
   TTS Engine (OpenAI nova → MP3)
        ↓
   Delivery (WhatsApp voice note / web / podcast)
```
