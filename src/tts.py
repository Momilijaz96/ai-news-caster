"""TTS generator - converts script text to MP3 audio using ElevenLabs."""

import os
from pathlib import Path

from elevenlabs.client import ElevenLabs

# Jessica — casual, friendly female voice
VOICE_ID = "cgSgspJ2msm6clMCkdW9"
MODEL_ID = "eleven_turbo_v2_5"


def generate_audio(script: str, output_path: str) -> str:
    """Generate MP3 audio from script text using ElevenLabs TTS."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY env var not set")

    client = ElevenLabs(api_key=api_key)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Strip stage directions that shouldn't be read aloud
    import re
    clean_script = re.sub(r'\[pause\]', '', script).strip()

    print(f"  Generating audio with ElevenLabs (Jessica)...")
    audio = client.text_to_speech.convert(
        text=clean_script,
        voice_id=VOICE_ID,
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
    )

    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    print(f"  Audio saved: {output_path}")
    return output_path
