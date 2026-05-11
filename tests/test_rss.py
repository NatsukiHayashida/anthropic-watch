"""Tests for RSS collector."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from src.collectors.rss import Article, fetch_feed, load_sources, collect_all


MOCK_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Anthropic News</title>
    <item>
      <title>Claude 4.7 Released</title>
      <link>https://www.anthropic.com/news/claude-4-7</link>
      <description>Announcing Claude 4.7 with improved capabilities.</description>
      <pubDate>Mon, 11 May 2026 00:00:00 GMT</pubDate>
      <guid>https://www.anthropic.com/news/claude-4-7</guid>
    </item>
    <item>
      <title>New Safety Research</title>
      <link>https://www.anthropic.com/research/safety-2026</link>
      <description>Our latest research on AI safety.</description>
      <pubDate>Sun, 10 May 2026 00:00:00 GMT</pubDate>
      <guid>https://www.anthropic.com/research/safety-2026</guid>
    </item>
  </channel>
</rss>"""


def test_article_content_hash():
    """Content hash should be deterministic."""
    a = Article(
        id="1",
        title="Test",
        url="https://example.com",
        summary="summary",
        published="2026-05-11",
        source_name="Test",
        source_category="公式",
    )
    assert len(a.content_hash()) == 16
    assert a.content_hash() == a.content_hash()  # deterministic


def test_fetch_feed():
    """fetch_feed should parse RSS XML into Article objects."""
    source = {"name": "Test Feed", "url": "https://example.com/rss", "category": "公式"}

    with patch("src.collectors.rss.feedparser.parse") as mock_parse:
        mock_feed = MagicMock()
        mock_entry1 = MagicMock()
        mock_entry1.get = lambda k, d="": {
            "id": "1",
            "title": "Claude 4.7 Released",
            "link": "https://example.com/1",
        }.get(k, d)
        mock_entry1.published = "Mon, 11 May 2026 00:00:00 GMT"
        mock_entry1.summary = "Announcing Claude 4.7"

        mock_feed.entries = [mock_entry1]
        mock_parse.return_value = mock_feed

        articles = fetch_feed(source)
        assert len(articles) == 1
        assert articles[0].title == "Claude 4.7 Released"
        assert articles[0].source_name == "Test Feed"


def test_load_sources():
    """load_sources should read YAML config correctly."""
    config_path = Path(__file__).parent.parent / "config" / "sources.yml"
    sources = load_sources(config_path)
    assert len(sources) >= 2  # At least 2 official sources
    assert all("name" in s and "url" in s and "category" in s for s in sources)
