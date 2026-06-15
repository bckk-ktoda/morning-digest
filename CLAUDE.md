# 朝の自動化パイプライン

Slack・Gmail・Google CalendarのデータからNotionのDaily Digest / Task Board / Knowledge Stockを一括更新する。

## 実行方法

```
/morning-run
```

## パイプライン構成

```
Phase 1（並列収集）:
  slack-collector (サブエージェント)
    └─ Slack/DM収集 → state/slack_raw.json
  gmail-collector (サブエージェント)
    └─ Gmail収集 → state/gmail_raw.json

Phase 2（合成）:
  morning-run 内の Python が slack_raw.json + gmail_raw.json → state/daily_context.json

Phase 3（並列処理。全員 state/*.json から読む。Notion Digestは再フェッチしない）:
  notion-writer (サブエージェント)
    └─ slack_raw.json + gmail_raw.json → Notion Daily Digest作成
  task-extractor (サブエージェント)
    └─ daily_context.json → Notion Task Board更新
  knowledge-curator (サブエージェント)
    └─ daily_context.json → Notion Knowledge Stock更新
```

## 固定ID

| 用途 | ID |
|------|----|
| Daily Digest 親ページ | `325fbe2a-3484-81df-b7d7-d543fed67f45` |
| Task Board DB | `1d842ae671874eeba4fd7ad23ca11bdc` |
| Task Board データソース | `collection://dd1cf269-1589-45f1-9e70-ca58152e1099` |
| Knowledge Stock 親ページ | `32dfbe2a34848087ae79c69769c70a21` |
| 自分のSlack UID | `UCGNFQ5L5` |
| 自分のメール | `ktoda@brightcove.com` |

## state/ ファイル

- `state/daily_context.json` — 当日の中間成果物（collector が書き込む）
- `state/run_status.json` — 実行ステータス
- `state/archive/YYYY-MM-DD/` — 日別アーカイブ（hooks が保存）

## 運用ルール

- Notionは最終書き込み先のみ。中間バスとして使わない
- task-extractor と knowledge-curator は必ず `state/daily_context.json` から読む（Notion Digestページを再フェッチしない）。ただし重複排除のための Task Board / Knowledge Stock の照合検索（search/fetch）は行ってよい
- `notion-update-data-source` の `in_trash: true` は絶対に使用しない
- **定例タスク（週末作業・月末作業・Atlassian Invoice）の冪等化:** 「同じ期限日の回は二度作らない」＋「未対応/対応中/保留の同種が在れば新しい回も作らない（1件をロール）」。判定は前回分の完了状況ではなく、対象期限と既存アクティブの有無で行う。期限日は task-extractor Step 0 の Python で決定的に算出する
- Googleカレンダーのツール名は `mcp__claude_ai_Google_Calendar__list_events` / `mcp__claude_ai_Google_Calendar__list_calendars`（旧 `gcal_*` は実在しない）
- 定期実行（routine）/clone 環境では `.claude/settings.local.json`（gitignore対象）の MCP 権限が効かないため、必要な MCP 許可は `.claude/settings.json` 側にも入れておく
