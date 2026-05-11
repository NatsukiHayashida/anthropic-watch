"""State management for seen articles (deduplication)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = "state/seen.json"


def load_seen(base_path: Path) -> dict:
    """Load seen article IDs from state file."""
    state_path = base_path / STATE_FILE
    if not state_path.exists():
        return {"seen_ids": {}, "last_run": None}

    with open(state_path) as f:
        return json.load(f)


def save_seen(base_path: Path, state: dict) -> None:
    """Save seen article IDs to state file."""
    state_path = base_path / STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with open(state_path, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def filter_new_articles(articles: list, state: dict) -> list:
    """Filter out already-seen articles. Returns only new ones."""
    seen_ids = set(state.get("seen_ids", {}).keys())
    new_articles = []

    for article in articles:
        article_key = article.content_hash()
        if article_key not in seen_ids:
            new_articles.append(article)

    return new_articles


def mark_as_seen(state: dict, articles: list) -> dict:
    """Mark articles as seen in state."""
    now = datetime.now(timezone.utc).isoformat()

    for article in articles:
        state["seen_ids"][article.content_hash()] = {
            "title": article.title,
            "url": article.url,
            "seen_at": now,
        }

    state["last_run"] = now

    # Keep only last 30 days of seen IDs to prevent unbounded growth
    cutoff_keys = []
    for key, val in state["seen_ids"].items():
        try:
            seen_at = datetime.fromisoformat(val["seen_at"])
            if (datetime.now(timezone.utc) - seen_at).days > 30:
                cutoff_keys.append(key)
        except (KeyError, ValueError):
            pass

    for key in cutoff_keys:
        del state["seen_ids"][key]

    return state
