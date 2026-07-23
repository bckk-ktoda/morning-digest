#!/usr/bin/env bash
# PreToolUse guard for morning-digest (defense-in-depth). Thin wrapper around
# guard_decide.py — the untrusted command string never touches the shell. Blocks
# dangerous primitives (network / exec / dynamic-code) and outbound tools while allowing
# the pipeline's benign json/date/pathlib python + `pip install jpholiday`.
# exit 0 = allow, exit 2 = block. Fails CLOSED on error.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "morning-digest guard: python3 unavailable — failing closed." >&2
  exit 2
fi
exec python3 "$DIR/guard_decide.py"
