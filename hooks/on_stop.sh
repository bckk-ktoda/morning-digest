#!/usr/bin/env bash
# 実行終了時に state/current の内容を日付別アーカイブへ保存する
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="$SCRIPT_DIR/../state"

DATE=$(date +%Y-%m-%d)
ARCHIVE_DIR="$STATE_DIR/archive/$DATE"
mkdir -p "$ARCHIVE_DIR"

for f in daily_context.json run_status.json; do
  if [ -f "$STATE_DIR/$f" ]; then
    cp "$STATE_DIR/$f" "$ARCHIVE_DIR/$f"
  fi
done
