"""Tests for output formatter."""

from src.formatter import build_daily_output


def test_empty_output():
    """No items should produce has_content=False."""
    output = build_daily_output([])
    assert output["has_content"] is False
    assert output["summary_line"] == "本日Anthropic新着なし"
    assert output["items_high"] == []


def test_categorization():
    """Items should be split by importance."""
    items = [
        {"importance": "high", "summary": "高1", "url": "https://a.com/1", "categories": ["新機能"]},
        {"importance": "high", "summary": "高2", "url": "https://a.com/2", "categories": ["モデル"]},
        {"importance": "medium", "summary": "中1", "url": "https://a.com/3", "categories": ["運用"]},
        {"importance": "low", "summary": "低1", "url": "https://a.com/4", "categories": ["その他"]},
        {"importance": "low", "summary": "低2", "url": "https://a.com/5", "categories": ["その他"]},
    ]
    output = build_daily_output(items)
    assert output["has_content"] is True
    assert len(output["items_high"]) == 2
    assert len(output["items_medium"]) == 1
    assert len(output["items_low_titles"]) == 2
    assert "高2件" in output["summary_line"]


def test_medium_limit():
    """Medium items should be capped at 3."""
    items = [
        {"importance": "medium", "summary": f"中{i}", "url": f"https://a.com/{i}", "categories": ["運用"]}
        for i in range(5)
    ]
    output = build_daily_output(items)
    assert len(output["items_medium"]) == 3


def test_low_titles_only():
    """Low items should contain title and URL only."""
    items = [
        {
            "importance": "low",
            "summary": "テスト記事",
            "url": "https://example.com",
            "categories": ["その他"],
            "translation_hint": "これは含まれない",
        }
    ]
    output = build_daily_output(items)
    low = output["items_low_titles"][0]
    assert "title" in low
    assert "url" in low
    assert "translation_hint" not in low
