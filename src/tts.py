"""TTS generator - converts script text to MP3 audio using edge-tts."""

import asyncio
from pathlib import Path

import edge_tts

DEFAULT_VOICE = "ur-PK-AsadNeural"


async def _generate_audio_async(script: str, output_path: str, voice: str) -> None:
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(output_path)


def generate_audio(script: str, output_path: str) -> str:
    """Generate MP3 audio from script text using edge-tts.

    edge-tts uses Microsoft Edge's TTS service and handles long text natively
    without chunking.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"  Generating audio with voice {DEFAULT_VOICE}...")
    asyncio.run(_generate_audio_async(script, output_path, DEFAULT_VOICE))

    print(f"  Audio saved: {output_path}")
    return output_path
