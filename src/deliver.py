"""WhatsApp delivery via openclaw CLI."""

import os
import shutil
import subprocess
from pathlib import Path


def deliver_whatsapp(audio_path: str, text: str) -> None:
    """Send MP3 voice note + English text summary to WhatsApp via openclaw.

    Args:
        audio_path: Path to the MP3 audio file (Urdu TTS briefing).
        text: English summary string to send as the WhatsApp text message.

    Requires:
        - openclaw installed and running locally
        - WHATSAPP_TARGET_NUMBER env var (E.164 format, e.g. +971501234567)
    """
    target = os.getenv("WHATSAPP_TARGET_NUMBER")
    if not target:
        raise ValueError("WHATSAPP_TARGET_NUMBER env var not set")

    # openclaw only allows media from its state dir or system tmp.
    # Copy the MP3 to ~/.openclaw/media/ before sending.
    media_dir = Path.home() / ".openclaw" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    staged = media_dir / Path(audio_path).name
    shutil.copy2(audio_path, staged)

    # 1. Send MP3 as voice note
    print(f"  Sending voice note to {target}...")
    subprocess.run([
        "openclaw", "message", "send",
        "--channel", "whatsapp",
        "--target", target,
        "--media", str(staged),
        "--message", "Your AI news briefing is ready",
    ], check=True)
    print("  Voice note sent.")

    # 2. Send English text summary
    print("  Sending text summary...")
    subprocess.run([
        "openclaw", "message", "send",
        "--channel", "whatsapp",
        "--target", target,
        "--message", text,
    ], check=True)
    print("  Summary sent.")
