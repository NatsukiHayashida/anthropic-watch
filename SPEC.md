# anthropic-watch 仕様書

> Anthropic / Claude 関連情報の自動キャッチアップシステム
> 既存curationメール（GAS+Claude API, 7:50 AM JST配信）に統合する

---

## 0. このドキュメントの位置付け

このドキュメントは Natsuki（@natsuki163）が Q（claude.ai）と相談して固めた仕様書である。CCはこの仕様に従って `~/claude-workspace/anthropic-watch/` 配下にシステムを構築する。

**判断の自由度**: 仕様書に明記がない実装詳細はCCの判断に委ねる（global CLAUDE.md の方針通り、最小確認で進める）。ただし以下については進める前に確認する：
- 月額コストが¥3,000を超える見込みの場合
- 既存システム（curationメール GAS、leapfrog 構造）への破壊的変更が必要な場合
- ユーザーの GitHub アカウント情報や API キーの新規発行が必要な場合

---

## 変更履歴

- 2026-05-09: 初版（Q作成）
- 2026-05-11: CC保存（Phase 1 MVP 構築開始）
