"""Tests for state management."""

import json
import tempfile
from pathlib import Path

from src.collectors.rss import Article
from src.state import load_seen, save_seen, filter_new_articles, mark_as_seen


def _make_article(title: str, url: str) -> Article:
    return Article(
        id=url,
        title=title,
        url=url,
        summary="test",
        published="2026-05-11",
        source_name="Test",
        source_category="公式",
    )


def test_load_seen_empty():
    """Loading from nonexistent file returns empty state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = load_seen(Path(tmpdir))
        assert state["seen_ids"] == {}
        assert state["last_run"] is None


def test_save_and_load():
    """State roundtrips through save/load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        state = {"seen_ids": {"abc123": {"title": "Test", "url": "https://example.com", "seen_at": "2026-05-11T00:00:00+00:00"}}, "last_run": "2026-05-11T00:00:00+00:00"}
        save_seen(base, state)
        loaded = load_seen(base)
        assert loaded["seen_ids"]["abc123"]["title"] == "Test"


def test_filter_new_articles():
    """Only articles not in seen state should pass through."""
    a1 = _make_article("Article 1", "https://example.com/1")
    a2 = _make_article("Article 2", "https://example.com/2")

    state = {"seen_ids": {a1.content_hash(): {"title": "Article 1"}}}
    new = filter_new_articles([a1, a2], state)
    assert len(new) == 1
    assert new[0].title == "Article 2"


def test_mark_as_seen():
    """mark_as_seen should add articles to state."""
    a1 = _make_article("Article 1", "https://example.com/1")
    state = {"seen_ids": {}, "last_run": None}
    updated = mark_as_seen(state, [a1])
    assert a1.content_hash() in updated["seen_ids"]
    assert updated["last_run"] is not None
