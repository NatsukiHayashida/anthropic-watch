"""Claude API processor for article curation and summarization."""

from __future__ import annotations

import json
import re
from pathlib import Path

import anthropic


MAX_API_CALLS_PER_DAY = 50
BATCH_SIZE = 10
MODEL = "claude-sonnet-4-6"


def load_prompt(base_path: Path) -> str:
    """Load the curation prompt template."""
    prompt_path = base_path / "prompts" / "curation.md"
    with open(prompt_path) as f:
        return f.read()


def build_articles_text(articles: list) -> str:
    """Format articles into text for the prompt."""
    parts = []
    for i, article in enumerate(articles, 1):
        parts.append(
            f"--- 記事 {i} ---\n"
            f"タイトル: {article.title}\n"
            f"URL: {article.url}\n"
            f"情報源: {article.source_name} ({article.source_category})\n"
            f"公開日: {article.published}\n"
            f"概要: {article.summary}\n"
        )
    return "\n".join(parts)


def extract_json(text: str) -> str:
    """Extract JSON from a response that might contain markdown code blocks."""
    # Try to find JSON array in code block
    match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try to find a bare JSON array
    match = re.search(r"(\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def process_batch(articles: list, system_prompt: str, client: anthropic.Anthropic) -> list[dict]:
    """Process a batch of articles with Claude API."""
    articles_text = build_articles_text(articles)

    user_message = (
        f"以下の{len(articles)}件の記事を判定してください。\n\n"
        f"{articles_text}\n\n"
        "全記事の判定結果をJSON配列で出力してください。\n"
        "```json で囲んで出力し、他のテキストは含めないでください。"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = response.content[0].text
    json_text = extract_json(response_text)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        print(f"  WARNING: JSON解析失敗。応答先頭200文字: {response_text[:200]}")
        return [
            {
                "importance": "low",
                "categories": ["その他"],
                "summary": a.title[:50],
                "translation_hint": None,
                "connection_note_seed": None,
                "url": a.url,
            }
            for a in articles
        ]


def process_with_fallback(articles: list, base_path: Path) -> list[dict]:
    """Process articles in batches with retry and fallback."""
    if not articles:
        return []

    system_prompt = load_prompt(base_path)
    client = anthropic.Anthropic()
    all_results: list[dict] = []

    # Split into batches
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(articles) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  バッチ {batch_num}/{total_batches} ({len(batch)}件)...")

        success = False
        for attempt in range(3):
            try:
                results = process_batch(batch, system_prompt, client)
                all_results.extend(results)
                success = True
                break
            except anthropic.APIError as e:
                print(f"    API エラー (試行 {attempt + 1}/3): {e}")
            except Exception as e:
                print(f"    エラー (試行 {attempt + 1}/3): {e}")

        if not success:
            print(f"    フォールバック: タイトル+URLのみ")
            all_results.extend(
                {
                    "importance": "low",
                    "categories": ["その他"],
                    "summary": a.title[:50],
                    "translation_hint": None,
                    "connection_note_seed": None,
                    "url": a.url,
                }
                for a in batch
            )

    return all_results
