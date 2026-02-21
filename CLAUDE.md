# CLAUDE.md — Project Context for Claude Code

## Project
AI News Caster — Daily AI news audio briefing system.

## Docs
- `docs/plan/raw-requirements.md` — Full requirements (read this first)
- `docs/plan/architecture.md` — System architecture & module responsibilities
- `docs/plan/PROGRESS.md` — What's done and what's next

## Current State (v0.1)
Core pipeline is built and functional:
- `src/aggregator.py` — RSS feed fetching + filtering
- `src/scriptwriter.py` — Claude-powered script generation
- `src/tts.py` — OpenAI TTS audio generation
- `src/main.py` — Pipeline orchestrator

## To Run
```bash
cp .env.example .env  # Add API keys
pip install -r requirements.txt
python -m src.main
```

## Key Decisions
- Python 3, keep it simple
- Claude for summarization, OpenAI for TTS
- Modular — each step is independent and swappable
- Build for personal use first, productize later
