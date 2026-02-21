from src.scriptwriter import extract_story_list


def test_extract_story_list_returns_list():
    entries = [
        {"title": "GPT-5 Released", "link": "https://openai.com/gpt5", "source": "OpenAI Blog", "summary": "...", "published": "2026-02-21", "priority": "high"},
        {"title": "Claude 4 Launches", "link": "https://anthropic.com/claude4", "source": "Anthropic", "summary": "...", "published": "2026-02-21", "priority": "high"},
    ]
    result = extract_story_list(entries, max_stories=8)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all("title" in s and "link" in s and "source" in s for s in result)


def test_extract_story_list_respects_max():
    entries = [
        {"title": f"Story {i}", "link": f"https://example.com/{i}", "source": "Test", "summary": "...", "published": "2026-02-21", "priority": "medium"}
        for i in range(20)
    ]
    result = extract_story_list(entries, max_stories=5)
    assert len(result) == 5


def test_extract_story_list_empty_entries():
    result = extract_story_list([], max_stories=8)
    assert result == []
