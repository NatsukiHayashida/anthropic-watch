"""RSS feed collector for Anthropic official and media sources."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import yaml


@dataclass
class Article:
    """A single article from an RSS feed."""

    id: str
    title: str
    url: str
    summary: str
    published: str
    source_name: str
    source_category: str

    def content_hash(self) -> str:
        return hashlib.sha256(f"{self.url}:{self.title}".encode()).hexdigest()[:16]


def load_sources(config_path: Path) -> list[dict]:
    """Load RSS sources from config/sources.yml."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    sources = []
    for section in ("official", "media"):
        if section in config and config[section]:
            sources.extend(config[section])
    return sources


def fetch_feed(source: dict) -> list[Article]:
    """Fetch and parse a single RSS feed."""
    feed = feedparser.parse(source["url"])
    articles = []

    for entry in feed.entries:
        article_id = entry.get("id") or entry.get("link", "")
        published = ""
        if hasattr(entry, "published"):
            published = entry.published
        elif hasattr(entry, "updated"):
            published = entry.updated

        summary = ""
        if hasattr(entry, "summary"):
            summary = entry.summary
        elif hasattr(entry, "description"):
            summary = entry.description

        # Strip HTML tags from summary
        if summary:
            from bs4 import BeautifulSoup

            summary = BeautifulSoup(summary, "html.parser").get_text(strip=True)
            # Truncate to reasonable length
            if len(summary) > 500:
                summary = summary[:500] + "..."

        articles.append(
            Article(
                id=article_id,
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                summary=summary,
                published=published,
                source_name=source["name"],
                source_category=source["category"],
            )
        )

    return articles


def collect_all(config_path: Path) -> list[Article]:
    """Collect articles from all configured RSS sources."""
    sources = load_sources(config_path)
    all_articles: list[Article] = []

    for source in sources:
        try:
            articles = fetch_feed(source)
            all_articles.extend(articles)
            print(f"  [{source['name']}] {len(articles)}件取得")
        except Exception as e:
            print(f"  [{source['name']}] 取得失敗: {e}")
            # Individual source failure: skip and continue
            continue

    return all_articles
