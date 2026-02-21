import json
from unittest.mock import patch


def test_summary_json_saved(tmp_path, monkeypatch):
    """summary.json must be written with title/link/source fields."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "audio").mkdir()
    (tmp_path / "archive").mkdir()
    (tmp_path / "config").mkdir()

    # Write a minimal config so load_config doesn't fail
    (tmp_path / "config" / "config.yaml").write_text("style:\n  max_stories: 8\n")

    fake_entries = [
        {"title": "Story A", "link": "https://a.com", "source": "SourceA",
         "summary": "...", "published": "2026-02-21", "priority": "high"},
    ]

    with patch("src.main.aggregate", return_value=fake_entries), \
         patch("src.main.write_script", return_value="This is the briefing script."), \
         patch("src.main.generate_audio", return_value=str(tmp_path / "audio/briefing-2026-02-21.mp3")), \
         patch("src.main.deliver_whatsapp"):
        from src.main import run
        run()

    summary_files = list(tmp_path.glob("archive/*-summary.json"))
    assert len(summary_files) == 1
    data = json.loads(summary_files[0].read_text())
    assert isinstance(data, list)
    assert data[0]["title"] == "Story A"
    assert data[0]["link"] == "https://a.com"
    assert data[0]["source"] == "SourceA"
