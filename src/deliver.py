"""WhatsApp delivery via openclaw CLI."""

import json
import os
import subprocess
from pathlib import Path


def deliver_whatsapp(audio_path: str, summary_path: str) -> None:
    """Send MP3 voice note + text summary to WhatsApp via openclaw.

    Requires:
        - openclaw installed and running locally
        - WHATSAPP_TARGET_NUMBER env var (E.164 format, e.g. +971501234567)
    """
    target = os.getenv("WHATSAPP_TARGET_NUMBER")
    if not target:
        raise ValueError("WHATSAPP_TARGET_NUMBER env var not set")

    # 1. Send MP3 as voice note
    print(f"  Sending voice note to {target}...")
    subprocess.run([
        "openclaw", "message", "send",
        "--channel", "whatsapp",
        "--target", target,
        "--media", audio_path,
        "--message", "🎙️ Your AI news briefing is ready",
    ], check=True)
    print("  Voice note sent.")

    # 2. Send text summary
    stories = json.loads(Path(summary_path).read_text())
    lines = ["*🎙️ Today's AI News*\n"]
    for i, story in enumerate(stories, 1):
        lines.append(f"{i}. *{story['title']}*")
        lines.append(f"   _{story['source']}_ — {story['link']}\n")
    lines.append("_Daily briefing by AI News Caster_")
    text = "\n".join(lines)

    print("  Sending text summary...")
    subprocess.run([
        "openclaw", "message", "send",
        "--channel", "whatsapp",
        "--target", target,
        "--message", text,
    ], check=True)
    print("  Summary sent.")
