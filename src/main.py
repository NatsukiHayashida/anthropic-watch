"""anthropic-watch main entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


def get_base_path() -> Path:
    """Get the project base path."""
    return Path(__file__).resolve().parent.parent


def run() -> None:
    """Main execution flow for daily watch."""
    base_path = get_base_path()
    load_dotenv(base_path / ".env")
    config_path = base_path / "config" / "sources.yml"

    print("=" * 50)
    print("anthropic-watch: 実行開始")
    print("=" * 50)

    # Step 1: Collect RSS articles
    from src.collectors.rss import collect_all

    print("\n[1/4] RSS収集中...")
    articles = collect_all(config_path)
    print(f"  合計 {len(articles)}件の記事を取得")

    if not articles:
        print("  記事なし。空の出力を生成します。")
        from src.formatter import build_daily_output, save_output

        output = build_daily_output([])
        output_path = save_output(base_path, output)
        print(f"\n出力: {output_path}")
        print("完了（新着なし）")
        return

    # Step 2: Filter new articles (dedup)
    from src.state import load_seen, filter_new_articles, mark_as_seen, save_seen

    print("\n[2/4] 既読フィルタリング...")
    state = load_seen(base_path)
    new_articles = filter_new_articles(articles, state)
    print(f"  新着 {len(new_articles)}件 / 既読 {len(articles) - len(new_articles)}件")

    if not new_articles:
        print("  全て既読。空の出力を生成します。")
        from src.formatter import build_daily_output, save_output

        output = build_daily_output([])
        output_path = save_output(base_path, output)
        state = mark_as_seen(state, articles)
        save_seen(base_path, state)
        print(f"\n出力: {output_path}")
        print("完了（新着なし）")
        return

    # Step 3: Process with Claude API
    from src.processor import process_with_fallback, MAX_API_CALLS_PER_DAY

    print("\n[3/4] Claude API で判定中...")
    if len(new_articles) > MAX_API_CALLS_PER_DAY:
        print(
            f"  WARNING: 記事数({len(new_articles)})が上限({MAX_API_CALLS_PER_DAY})を超えています。"
            f"  上位{MAX_API_CALLS_PER_DAY}件のみ処理します。"
        )
        new_articles = new_articles[:MAX_API_CALLS_PER_DAY]

    curated = process_with_fallback(new_articles, base_path)
    print(f"  {len(curated)}件の判定完了")

    # Step 4: Format and save
    from src.formatter import build_daily_output, save_output

    print("\n[4/4] 出力生成中...")
    output = build_daily_output(curated)
    output_path = save_output(base_path, output)

    # Update seen state
    state = mark_as_seen(state, new_articles)
    save_seen(base_path, state)

    # Summary
    print(f"\n出力: {output_path}")
    print(f"サマリー: {output['summary_line']}")
    print("完了")


def run_append_leapfrog() -> None:
    """Append high-importance items to leapfrog/anthropic-watch.md (local only)."""
    import json
    from datetime import datetime, timezone, timedelta

    base_path = get_base_path()
    output_path = base_path / "docs" / "daily-output.json"
    leapfrog_path = Path.home() / "work" / "leapfrog" / "anthropic-watch.md"

    if not output_path.exists():
        print("daily-output.json が見つかりません。先に通常実行してください。")
        return

    with open(output_path) as f:
        data = json.load(f)

    if not data.get("has_content") or not data.get("items_high"):
        print("高重要度アイテムなし。leapfrog追記をスキップします。")
        return

    # Build markdown
    jst = timezone(timedelta(hours=9))
    date_str = data.get("date", datetime.now(jst).strftime("%Y-%m-%d"))

    lines = [f"\n## {date_str}\n"]
    for item in data["items_high"]:
        categories = ", ".join(item.get("categories", []))
        lines.append(f"### [{categories}] {item.get('summary', '')}")
        lines.append(f"- 要約: {item.get('summary', '')}")
        lines.append(f"- 出典: {item.get('url', '')}")
        if item.get("translation_hint"):
            lines.append(f"- 翻訳ヒント: {item['translation_hint']}")
        if item.get("connection_note_seed"):
            lines.append(f"- 接続ノート候補: {item['connection_note_seed']}")
        lines.append("")

    content = "\n".join(lines)

    # Append or create
    leapfrog_path.parent.mkdir(parents=True, exist_ok=True)
    if leapfrog_path.exists():
        with open(leapfrog_path, "a") as f:
            f.write(content)
    else:
        with open(leapfrog_path, "w") as f:
            f.write("# Anthropic Watch — 高重要度ログ\n")
            f.write(content)

    print(f"leapfrog追記完了: {leapfrog_path}")


if __name__ == "__main__":
    if "--append-leapfrog" in sys.argv:
        run_append_leapfrog()
    else:
        run()
