"""TTS generator - converts script text to MP3 audio using OpenAI TTS."""

import openai
import yaml
from pathlib import Path


def load_config(config_path: str = "config/config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def generate_audio(script: str, output_path: str, config_path: str = "config/config.yaml") -> str:
    """Generate MP3 audio from script text using OpenAI TTS.

    OpenAI TTS has a 4096 character limit per request, so we split long scripts
    into chunks and concatenate the resulting audio.
    """
    config = load_config(config_path)
    tts_config = config.get("tts", {})
    voice = tts_config.get("voice", "nova")
    speed = tts_config.get("speed", 1.0)

    client = openai.OpenAI()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Split script into chunks under 4096 chars, breaking at sentence boundaries
    chunks = _split_script(script, max_chars=4096)
    print(f"  Generating audio in {len(chunks)} chunk(s)...")

    if len(chunks) == 1:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            speed=speed,
            input=chunks[0],
        )
        response.write_to_file(output_path)
    else:
        # Generate each chunk and concatenate the raw MP3 bytes
        audio_bytes = b""
        for i, chunk in enumerate(chunks, 1):
            print(f"    Chunk {i}/{len(chunks)} ({len(chunk)} chars)...")
            response = client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                speed=speed,
                input=chunk,
            )
            audio_bytes += response.read()

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

    print(f"  Audio saved: {output_path}")
    return output_path


def _split_script(text: str, max_chars: int = 4096) -> list[str]:
    """Split text into chunks at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break

        # Find a good break point (end of sentence) within limit
        split_at = max_chars
        for sep in [". ", "! ", "? ", "\n"]:
            idx = remaining[:max_chars].rfind(sep)
            if idx > max_chars // 2:
                split_at = idx + len(sep)
                break

        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:]

    return chunks
