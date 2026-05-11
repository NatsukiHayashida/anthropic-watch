"""Format curated articles into daily output JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))
OUTPUT_FILE = "docs/daily-output.json"


def build_daily_output(curated_items: list[dict]) -> dict:
    """Build the daily output JSON structure."""
    now = datetime.now(JST)

    if not curated_items:
        return {
            "date": now.strftime("%Y-%m-%d"),
            "generated_at": now.isoformat(),
            "summary_line": "本日Anthropic新着なし",
            "items_high": [],
            "items_medium": [],
            "items_low_titles": [],
            "has_content": False,
        }

    # Separate by importance
    high = [item for item in curated_items if item.get("importance") == "high"]
    medium = [item for item in curated_items if item.get("importance") == "medium"]
    low = [item for item in curated_items if item.get("importance") == "low"]

    # Apply limits per spec: high=all, medium=max 3, low=titles only (max 5)
    medium = medium[:3]
    low_titles = [
        {"title": item.get("summary", ""), "url": item.get("url", "")}
        for item in low[:5]
    ]

    summary_line = f"本日Anthropic新着: 高{len(high)}件 / 中{len(medium)}件 / 低{len(low_titles)}件"

    return {
        "date": now.strftime("%Y-%m-%d"),
        "generated_at": now.isoformat(),
        "summary_line": summary_line,
        "items_high": high,
        "items_medium": medium,
        "items_low_titles": low_titles,
        "has_content": True,
    }


def save_output(base_path: Path, output: dict) -> Path:
    """Save daily output to docs/daily-output.json."""
    output_path = base_path / OUTPUT_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return output_path
