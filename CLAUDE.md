# 朝の自動化パイプライン

Slack・Gmail・Google CalendarのデータからNotionのDaily Digest / Task Board / Knowledge Stockを一括更新する。

## 実行方法

```
/morning-run
```

## パイプライン構成

```
collector (サブエージェント)
  └─ Slack/Gmail/Calendar収集 → state/daily_context.json + Notion Daily Digest作成

並列実行:
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
- task-extractor と knowledge-curator は必ず `state/daily_context.json` から読む（Notion Digestページを再フェッチしない）
- `notion-update-data-source` の `in_trash: true` は絶対に使用しない
