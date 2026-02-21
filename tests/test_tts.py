"""Tests for src/tts.py using ElevenLabs."""

from pathlib import Path
from unittest.mock import MagicMock, patch


def test_generate_audio_calls_elevenlabs_with_correct_params(tmp_path):
    """generate_audio should call ElevenLabs TTS with correct voice and model."""
    output_path = str(tmp_path / "output.mp3")
    script = "Hello, this is a test briefing."

    mock_audio_chunks = [b"chunk1", b"chunk2"]

    with patch("src.tts.ElevenLabs") as mock_client_cls, \
         patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key"}):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = iter(mock_audio_chunks)

        from src.tts import generate_audio, VOICE_ID, MODEL_ID
        result = generate_audio(script, output_path)

    mock_client.text_to_speech.convert.assert_called_once_with(
        text=script,
        voice_id=VOICE_ID,
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
    )
    assert result == output_path
    assert Path(output_path).read_bytes() == b"chunk1chunk2"


def test_generate_audio_creates_parent_directory(tmp_path):
    """generate_audio should create the parent directory if it does not exist."""
    output_path = str(tmp_path / "nested" / "dir" / "output.mp3")

    with patch("src.tts.ElevenLabs") as mock_client_cls, \
         patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key"}):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.text_to_speech.convert.return_value = iter([b"audio"])

        from src.tts import generate_audio
        generate_audio("Test.", output_path)

    assert Path(output_path).parent.exists()


def test_generate_audio_raises_without_api_key(tmp_path):
    """generate_audio should raise ValueError if ELEVENLABS_API_KEY is not set."""
    import os
    env = {k: v for k, v in os.environ.items() if k != "ELEVENLABS_API_KEY"}

    with patch.dict("os.environ", env, clear=True):
        import importlib
        import src.tts
        importlib.reload(src.tts)
        from src.tts import generate_audio
        try:
            generate_audio("Test.", str(tmp_path / "out.mp3"))
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "ELEVENLABS_API_KEY" in str(e)
