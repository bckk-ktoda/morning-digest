---
description: 朝の自動化パイプラインを一括実行する（Digest作成 → Task更新 → Knowledge更新）
---

## 実行指示

以下の順序でサブエージェントを実行してください。確認なしに即実行すること。

---

### Phase 1: 並列収集

claude-task-viewerにタスクを登録する:

```bash
python3 -c "
import json, pathlib
d = pathlib.Path.home() / '.claude/tasks/morning-digest'
d.mkdir(parents=True, exist_ok=True)
tasks = [
  {'id':'1','subject':'📡 slack-collector','description':'Slackメッセージ収集 → slack_raw.json','activeForm':'実行中...','status':'in_progress','blocks':['3','4','5'],'blockedBy':[]},
  {'id':'2','subject':'📧 gmail-collector','description':'Gmail収集 → gmail_raw.json','activeForm':'実行中...','status':'in_progress','blocks':['3','4','5'],'blockedBy':[]},
  {'id':'3','subject':'📋 notion-writer','description':'Notion Daily Digest作成','activeForm':'待機中','status':'pending','blocks':[],'blockedBy':['1','2']},
  {'id':'4','subject':'📌 task-extractor','description':'Task Board更新','activeForm':'待機中','status':'pending','blocks':[],'blockedBy':['1','2']},
  {'id':'5','subject':'📚 knowledge-curator','description':'Knowledge Stock更新','activeForm':'待機中','status':'pending','blocks':[],'blockedBy':['1','2']},
]
for t in tasks:
  (d / f\"{t['id']}.json\").write_text(json.dumps(t, ensure_ascii=False, indent=2))
print('tasks initialized')
"
```

`slack-collector` と `gmail-collector` サブエージェントを**並列で**起動する:
- `slack-collector`: Slack/DMを収集し `state/slack_raw.json` を保存する
- `gmail-collector`: Gmailを収集し `state/gmail_raw.json` を保存する

---

### Phase 2: daily_context.json を合成

両エージェントが完了し `state/slack_raw.json` と `state/gmail_raw.json` が揃ったことを確認してから、以下のBashコマンドで合成する:

```bash
python3 << 'EOF'
import json, pathlib

slack = json.loads(pathlib.Path('state/slack_raw.json').read_text())
gmail = json.loads(pathlib.Path('state/gmail_raw.json').read_text())

context = {
  "metadata": slack["metadata"],
  "notion_digest_page_id": None,
  "action_items": slack["action_items"] + gmail["action_items"],
  "knowledge_candidates": slack["knowledge_candidates"] + gmail["knowledge_candidates"]
}

pathlib.Path('state/daily_context.json').write_text(
  json.dumps(context, ensure_ascii=False, indent=2)
)
print(f"daily_context.json created: {len(context['action_items'])} action_items, {len(context['knowledge_candidates'])} knowledge_candidates")
EOF
```

claude-task-viewerを更新する:

```bash
python3 -c "
import json, pathlib
d = pathlib.Path.home() / '.claude/tasks/morning-digest'
for i in ['1','2']:
  t = json.loads((d/f'{i}.json').read_text())
  t['status'] = 'completed'; t['activeForm'] = '完了'
  (d/f'{i}.json').write_text(json.dumps(t, ensure_ascii=False, indent=2))
for i in ['3','4','5']:
  t = json.loads((d/f'{i}.json').read_text())
  t['status'] = 'in_progress'; t['activeForm'] = '実行中...'; t['blockedBy'] = []
  (d/f'{i}.json').write_text(json.dumps(t, ensure_ascii=False, indent=2))
print('phase 2 done')
"
```

---

### Phase 3: 並列処理

以下の3つのサブエージェントを**並列で**起動する（全員 `state/daily_context.json` または `state/*_raw.json` から読む。Notionは再フェッチしない）:

- `notion-writer` サブエージェント: slack_raw.json + gmail_raw.json → Notion Daily Digest作成
- `task-extractor` サブエージェント: daily_context.json → Task Board更新
- `knowledge-curator` サブエージェント: daily_context.json → Knowledge Stock更新

全エージェント完了後:

```bash
python3 -c "
import json, pathlib
d = pathlib.Path.home() / '.claude/tasks/morning-digest'
for i in ['3','4','5']:
  t = json.loads((d/f'{i}.json').read_text())
  t['status'] = 'completed'; t['activeForm'] = '完了'
  (d/f'{i}.json').write_text(json.dumps(t, ensure_ascii=False, indent=2))
print('all done')
"
```

---

### Phase 4: 完了レポート

各エージェントの実行結果をまとめて以下のフォーマットで出力する:

```
🌅 朝のパイプライン完了レポート（YYYY-MM-DD）

📡 収集
  ✅ Slack: [チャンネル数]チャンネル、DM確認済み
  ✅ Gmail: [件数]件処理

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
    "slack_collector": "success|failed",
    "gmail_collector": "success|failed",
    "notion_writer": "success|failed|skipped",
    "task_extractor": "success|failed|skipped",
    "knowledge_curator": "success|failed|skipped"
  }
}
```
