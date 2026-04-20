---
description: 朝の自動化パイプラインを一括実行する（Digest作成 → Task更新 → Knowledge更新）
---

## 実行指示

以下の順序でサブエージェントを実行してください。確認なしに即実行すること。

---

### Phase 1: 情報収集とDigest作成

まず以下のBashコマンドを実行してclaude-task-viewerにタスクを登録する:

```bash
python3 -c "
import json, pathlib
d = pathlib.Path.home() / '.claude/tasks/morning-digest'
d.mkdir(parents=True, exist_ok=True)
tasks = [
  {'id':'1','subject':'🌅 collector','description':'Slack/Gmail/Calendar収集 → Notion Digest作成','activeForm':'実行中...','status':'in_progress','blocks':['2','3'],'blockedBy':[]},
  {'id':'2','subject':'📌 task-extractor','description':'Task Board更新','activeForm':'待機中','status':'pending','blocks':[],'blockedBy':['1']},
  {'id':'3','subject':'📚 knowledge-curator','description':'Knowledge Stock更新','activeForm':'待機中','status':'pending','blocks':[],'blockedBy':['1']},
]
for t in tasks:
  (d / f\"{t['id']}.json\").write_text(json.dumps(t, ensure_ascii=False, indent=2))
print('tasks initialized')
"
```

次に `collector` サブエージェントを起動して実行する。

このエージェントは:
- Slack/Gmail/Calendarからデータを収集する
- Notion Daily Digestページを作成する
- `state/daily_context.json` に構造化データを保存する

**Phase 1が完了し `state/daily_context.json` が存在することを確認してから:**

以下のBashコマンドでclaude-task-viewerのステータスを更新する:

```bash
python3 -c "
import json, pathlib
d = pathlib.Path.home() / '.claude/tasks/morning-digest'
(d/'1.json').write_text(json.dumps({'id':'1','subject':'🌅 collector','description':'Slack/Gmail/Calendar収集 → Notion Digest作成','activeForm':'完了','status':'completed','blocks':['2','3'],'blockedBy':[]}, ensure_ascii=False, indent=2))
(d/'2.json').write_text(json.dumps({'id':'2','subject':'📌 task-extractor','description':'Task Board更新','activeForm':'実行中...','status':'in_progress','blocks':[],'blockedBy':[]}, ensure_ascii=False, indent=2))
(d/'3.json').write_text(json.dumps({'id':'3','subject':'📚 knowledge-curator','description':'Knowledge Stock更新','activeForm':'実行中...','status':'in_progress','blocks':[],'blockedBy':[]}, ensure_ascii=False, indent=2))
print('phase 1 done')
"
```

---

### Phase 2: 並列処理

以下の2つのサブエージェントを**並列で**起動する（どちらも `state/daily_context.json` を読み込む。Notion Digestページは再フェッチしない）:

- `task-extractor` サブエージェント: Task Boardを更新する
- `knowledge-curator` サブエージェント: Knowledge Stockを更新する

両エージェント完了後、以下のBashコマンドでステータスを更新する:

```bash
python3 -c "
import json, pathlib
d = pathlib.Path.home() / '.claude/tasks/morning-digest'
(d/'2.json').write_text(json.dumps({'id':'2','subject':'📌 task-extractor','description':'Task Board更新','activeForm':'完了','status':'completed','blocks':[],'blockedBy':[]}, ensure_ascii=False, indent=2))
(d/'3.json').write_text(json.dumps({'id':'3','subject':'📚 knowledge-curator','description':'Knowledge Stock更新','activeForm':'完了','status':'completed','blocks':[],'blockedBy':[]}, ensure_ascii=False, indent=2))
print('phase 2 done')
"
```

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
