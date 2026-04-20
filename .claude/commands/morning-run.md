---
description: 朝の自動化パイプラインを一括実行する（Digest作成 → Task更新 → Knowledge更新）
---

## 実行指示

以下の順序でサブエージェントを実行してください。確認なしに即実行すること。

---

### Phase 1: 情報収集とDigest作成

`collector` サブエージェントを起動して実行する。

このエージェントは:
- Slack/Gmail/Calendarからデータを収集する
- Notion Daily Digestページを作成する
- `state/daily_context.json` に構造化データを保存する

**Phase 1が完了し `state/daily_context.json` が存在することを確認してから Phase 2 に進む。**

---

### Phase 2: 並列処理

以下の2つのサブエージェントを**並列で**起動する（どちらも `state/daily_context.json` を読み込む。Notion Digestページは再フェッチしない）:

- `task-extractor` サブエージェント: Task Boardを更新する
- `knowledge-curator` サブエージェント: Knowledge Stockを更新する

---

### Phase 3: 完了レポート

各エージェントの実行結果をまとめて以下のフォーマットで出力する:

```
🌅 朝のパイプライン完了レポート（YYYY-MM-DD）

📋 Daily Digest
  ✅ Notionページ作成: [ページURL]

📌 Task Board
  [task-extractorの結果サマリー]

📚 Knowledge Stock
  [knowledge-curatorの結果サマリー]

⏱ 実行時間: XX分XX秒
```

その後 `state/run_status.json` に実行ログを保存する:
```json
{
  "date": "YYYY-MM-DD",
  "completed_at": "ISO8601",
  "phases": {
    "collector": "success|failed",
    "task_extractor": "success|failed|skipped",
    "knowledge_curator": "success|failed|skipped"
  }
}
```
