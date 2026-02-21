"""AI News Caster - main pipeline entry point."""

import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.aggregator import aggregate
from src.scriptwriter import write_script, write_whatsapp_summary, extract_story_list, load_config
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

    # Step 2a: Write punchy audio teaser script
    print(f"\n[2/4] Writing audio teaser ({len(entries)} entries)...")
    script = write_script(entries)
    script_path = f"scripts/briefing-{today}.txt"
    Path(script_path).parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script)
    print(f"  Script saved: {script_path}")

    # Step 2b: Write detailed WhatsApp summary
    print(f"\n[3/4] Writing WhatsApp summary...")
    whatsapp_text = write_whatsapp_summary(entries)

    # Step 3: Generate audio
    print(f"\n[4/4] Generating audio...")
    audio_path = f"audio/briefing-{today}.mp3"
    try:
        generate_audio(script, audio_path)
    except Exception as e:
        print(f"  Error: TTS generation failed: {e}")
        sys.exit(1)

    # Archive
    archive_path = f"archive/{today}.json"
    Path(archive_path).parent.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    max_stories = cfg.get("style", {}).get("max_stories", 8)
    with open(archive_path, "w") as f:
        json.dump({
            "date": today,
            "entries_found": len(entries),
            "entries": entries,
            "script_path": script_path,
            "audio_path": audio_path,
            "script_word_count": len(script.split()),
            "top_stories": extract_story_list(entries, max_stories=max_stories),
        }, f, indent=2, default=str)
    print(f"  Archive saved: {archive_path}")

    # Deliver: audio teaser + detailed text summary
    print(f"\n[+] Delivering via WhatsApp...")
    try:
        deliver_whatsapp(audio_path, whatsapp_text)
    except Exception as e:
        print(f"  Warning: WhatsApp delivery failed: {e}")
        print("  Briefing saved locally — deliver manually if needed.")

    print(f"\n=== Done! ===")
    print(f"  Script:  {script_path}")
    print(f"  Audio:   {audio_path}")
    print(f"  Archive: {archive_path}\n")


if __name__ == "__main__":
    run()
