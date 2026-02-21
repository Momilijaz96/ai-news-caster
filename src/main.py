"""AI News Caster - main pipeline entry point."""

import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.aggregator import aggregate
from src.scriptwriter import write_urdu_script, write_english_summary, extract_story_list, load_config
from src.tts import generate_audio
from src.deliver import deliver_whatsapp


def run():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n=== AI News Caster - {today} ===\n")

    # Step 1: Aggregate news
    print("[1/4] Aggregating news from RSS feeds...")
    entries = aggregate()

    if not entries:
        print("No news entries found. Try increasing hours_back or checking feed URLs.")
        sys.exit(1)

    # Step 2a: Write Urdu script for TTS audio
    print(f"\n[2/4] Writing Urdu script for audio ({len(entries)} entries to review)...")
    urdu_script = write_urdu_script(entries)

    # Save Urdu script
    urdu_script_path = f"scripts/briefing-{today}-urdu.txt"
    Path(urdu_script_path).parent.mkdir(parents=True, exist_ok=True)
    with open(urdu_script_path, "w", encoding="utf-8") as f:
        f.write(urdu_script)
    print(f"  Urdu script saved: {urdu_script_path}")

    # Step 2b: Write English summary for WhatsApp text
    print(f"\n[3/4] Writing English summary for WhatsApp...")
    english_summary = write_english_summary(entries)
    print(f"  English summary ready ({len(english_summary.split())} words)")

    # Step 3: Generate audio from Urdu script
    print(f"\n[4/4] Generating audio...")
    audio_path = f"audio/briefing-{today}.mp3"
    try:
        generate_audio(urdu_script, audio_path)
    except Exception as e:
        print(f"  Error: TTS generation failed: {e}")
        sys.exit(1)

    # Archive
    archive_path = f"archive/{today}.json"
    Path(archive_path).parent.mkdir(parents=True, exist_ok=True)
    archive_data = {
        "date": today,
        "entries_found": len(entries),
        "entries": entries,
        "urdu_script_path": urdu_script_path,
        "audio_path": audio_path,
        "urdu_script_word_count": len(urdu_script.split()),
    }
    with open(archive_path, "w") as f:
        json.dump(archive_data, f, indent=2, default=str)
    print(f"  Archive saved: {archive_path}")

    # Save summary JSON for archive (kept for compatibility)
    cfg = load_config()
    max_stories = cfg.get("style", {}).get("max_stories", 8)
    summary = extract_story_list(entries, max_stories=max_stories)
    summary_path = f"archive/{today}-summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary saved: {summary_path}")

    # Step 5: Deliver via WhatsApp
    print(f"\n[5/5] Delivering via WhatsApp...")
    try:
        deliver_whatsapp(audio_path, english_summary)
    except Exception as e:
        print(f"  Warning: WhatsApp delivery failed: {e}")
        print("  Briefing saved locally — deliver manually if needed.")

    print(f"\n=== Done! ===")
    print(f"  Urdu script: {urdu_script_path}")
    print(f"  Audio:       {audio_path}")
    print(f"  Archive:     {archive_path}")
    print(f"  Summary:     {summary_path}\n")


if __name__ == "__main__":
    run()
