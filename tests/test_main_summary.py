import json
from unittest.mock import patch


def test_archive_json_saved(tmp_path, monkeypatch):
    """archive JSON must include top_stories with title/link/source fields."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "audio").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "config").mkdir()

    (tmp_path / "config" / "config.yaml").write_text("style:\n  max_stories: 8\nllm:\n  model: claude-sonnet-4-20250514\n  max_tokens: 4000\n")

    fake_entries = [
        {"title": "Story A", "link": "https://a.com", "source": "SourceA",
         "summary": "...", "published": "2026-02-22", "priority": "high"},
    ]

    with patch("src.main.aggregate", return_value=fake_entries), \
         patch("src.main.write_script", return_value="Audio teaser script."), \
         patch("src.main.write_whatsapp_summary", return_value="WhatsApp summary text."), \
         patch("src.main.generate_audio", return_value=str(tmp_path / "audio/briefing.mp3")), \
         patch("src.main.deliver_whatsapp"):
        from src.main import run
        run()

    archive_files = list(tmp_path.glob("archive/*.json"))
    assert len(archive_files) == 1
    data = json.loads(archive_files[0].read_text())
    assert "top_stories" in data
    assert data["top_stories"][0]["title"] == "Story A"
    assert data["top_stories"][0]["link"] == "https://a.com"
    assert data["top_stories"][0]["source"] == "SourceA"
