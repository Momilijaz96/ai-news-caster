"""AI News Caster - main pipeline entry point."""

import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.aggregator import aggregate
from src.scriptwriter import write_script, extract_story_list, load_config
from src.tts import generate_audio


def run():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n=== AI News Caster - {today} ===\n")

    # Step 1: Aggregate news
    print("[1/3] Aggregating news from RSS feeds...")
    entries = aggregate()

    if not entries:
        print("No news entries found. Try increasing hours_back or checking feed URLs.")
        sys.exit(1)

    # Step 2: Write script with Claude
    print(f"\n[2/3] Writing briefing script ({len(entries)} entries to review)...")
    script = write_script(entries)

    # Save script
    script_path = f"scripts/briefing-{today}.txt"
    Path(script_path).parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script)
    print(f"  Script saved: {script_path}")

    # Step 3: Generate audio
    print(f"\n[3/3] Generating audio...")
    audio_path = f"audio/briefing-{today}.mp3"
    generate_audio(script, audio_path)

    # Step 4: Archive
    archive_path = f"archive/{today}.json"
    Path(archive_path).parent.mkdir(parents=True, exist_ok=True)
    archive_data = {
        "date": today,
        "entries_found": len(entries),
        "entries": entries,
        "script_path": script_path,
        "audio_path": audio_path,
        "script_word_count": len(script.split()),
    }
    with open(archive_path, "w") as f:
        json.dump(archive_data, f, indent=2, default=str)
    print(f"  Archive saved: {archive_path}")

    # Save summary for WhatsApp delivery
    cfg = load_config()
    max_stories = cfg.get("style", {}).get("max_stories", 8)
    summary = extract_story_list(entries, max_stories=max_stories)
    summary_path = f"archive/{today}-summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary saved: {summary_path}")

    print(f"\n=== Done! ===")
    print(f"  Script: {script_path}")
    print(f"  Audio:  {audio_path}")
    print(f"  Archive: {archive_path}")
    print(f"  Summary: {summary_path}\n")


if __name__ == "__main__":
    run()
