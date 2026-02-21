"""Tests for src/tts.py using edge-tts."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.tts import generate_audio


def test_generate_audio_calls_communicate_with_correct_voice(tmp_path):
    """generate_audio should call edge_tts.Communicate with en-US-JennyNeural."""
    output_path = str(tmp_path / "output.mp3")
    script = "Hello, this is a test briefing."

    mock_communicate_instance = MagicMock()
    mock_communicate_instance.save = AsyncMock()

    with patch("src.tts.edge_tts.Communicate", return_value=mock_communicate_instance) as mock_communicate:
        result = generate_audio(script, output_path)

    mock_communicate.assert_called_once_with(script, "en-US-JennyNeural")
    mock_communicate_instance.save.assert_awaited_once_with(output_path)
    assert result == output_path


def test_generate_audio_creates_parent_directory(tmp_path):
    """generate_audio should create the parent directory if it does not exist."""
    output_path = str(tmp_path / "nested" / "dir" / "output.mp3")
    script = "Test script."

    mock_communicate_instance = MagicMock()
    mock_communicate_instance.save = AsyncMock()

    with patch("src.tts.edge_tts.Communicate", return_value=mock_communicate_instance):
        generate_audio(script, output_path)

    from pathlib import Path
    assert Path(output_path).parent.exists()


def test_generate_audio_no_openai_import():
    """src.tts should not import openai."""
    import sys

    # Remove cached module to force fresh inspection
    for mod in list(sys.modules.keys()):
        if mod == "src.tts":
            del sys.modules[mod]

    import src.tts as tts_module
    import inspect
    source = inspect.getsource(tts_module)
    assert "import openai" not in source
    assert "openai" not in source
