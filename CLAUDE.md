# anthropic-watch CC作業指針

## プロジェクト概要
Anthropic/Claude関連情報の自動キャッチアップシステム。
毎朝6:30 JSTにGitHub Actionsで実行し、既存curationメールに統合する。

## ディレクトリ構成
- `src/` - メインソースコード
- `config/` - 設定ファイル（sources.yml, docs-pages.yml）
- `prompts/` - Claude APIプロンプト
- `state/` - 既読管理（自動コミット対象）
- `docs/` - 出力JSON（GitHub Pages公開）
- `tests/` - テスト

## 実行コマンド
- 通常実行: `uv run python -m src.main`
- leapfrog追記: `uv run python -m src.main --append-leapfrog`
- テスト: `uv run pytest`

## 開発方針
- SPEC.mdに従う
- 個別情報源の失敗は他に影響させない
- Claude API失敗時はタイトル+URLのみでフォールバック
- 1日50件上限（暴発防止）
