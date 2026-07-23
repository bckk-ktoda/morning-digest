#!/usr/bin/env python3
"""
PreToolUse decision for morning-digest. Invoked by hooks/guard.sh.

morning-digest legitimately runs inline python (json / pathlib / datetime / pytz /
zoneinfo / jpholiday) via heredocs, plus `pip install jpholiday`, so we CANNOT use the
strict allowlist-dispatcher approach reply-draft uses (it would break the pipeline).

Instead this is DEFENSE-IN-DEPTH: it blocks the dangerous primitives an injected message
could use to exfiltrate data, execute a shell, or run dynamic code — none of which the
legitimate pipeline uses — while allowing its benign data/date python. This is a denylist
and therefore NOT a hard guarantee (obfuscation can bypass it); the robust guarantee is to
refactor the heredocs into fixed scripts + an allowlist dispatcher (see reply-draft). It
also blocks all outbound send tools and dangerous shell binaries via tool_name.

Exit 0 = allow, exit 2 = block. Fails CLOSED on unparseable payload.
"""
import sys, os, re, json, datetime

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "state", "guard.log")


def _log(msg: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def _block(reason: str, detail: str = "") -> None:
    _log(f"BLOCKED [{detail}]: {reason}")
    print(f"morning-digest guard: BLOCKED — {reason}", file=sys.stderr)
    sys.exit(2)


# Outbound / irreversible MCP tools the pipeline never uses — block if an injection tries.
FORBIDDEN_MCP = re.compile(
    r"slack_send_message|slack_send_message_draft|slack_schedule_message|slack_add_reaction"
    r"|slack_create_canvas|slack_update_canvas"
    r"|Gmail__(create_draft|update_draft|create_label|delete_label|update_label"
    r"|label_message|label_thread|unlabel_message|unlabel_thread|apply_sensitive)"
    r"|notion-update-data-source"
)

# Dangerous primitives that the LEGIT pipeline never contains. Conservative — only tokens
# that are clearly never part of benign json/date/pathlib python or the pip/npx it uses.
DANGEROUS = [
    # network egress
    "socket", "urllib", "requests", "http.client", "httplib", "ftplib", "smtplib",
    "telnetlib", "/dev/tcp", "asyncio.open_connection", "aiohttp",
    # process / shell execution
    "subprocess", "os.system", "os.popen", "os.exec", "os.spawn", "pty.spawn",
    "getoutput", "multiprocessing",
    # dynamic code
    "__import__", "eval(", "exec(", "compile(", "importlib", "ctypes", "cffi",
    "marshal.loads", "pickle.loads", "codecs.decode",
    # sensitive files
    ".ssh", "id_rsa", "id_ed25519", ".netrc", ".aws/credentials", "keychain",
]
DANGEROUS_RE = re.compile("|".join(re.escape(t) for t in DANGEROUS), re.I)
# Shell chaining into an interpreter / dangerous binaries (word-boundary to avoid false hits).
SHELL_DANGER = re.compile(
    r"\|\s*(sh|bash|zsh|python3?|perl|ruby)\b"      # pipe into an interpreter
    r"|\b(bash|sh|zsh)\s+-c\b"                        # sh -c "..."
    r"|\b(curl|wget|nc|ncat|netcat|ssh|scp|sftp|telnet|osascript|launchctl|crontab|security|defaults|npm|npx)\b"
    r"|\beval\b",
    re.I,
)
# The pipeline installs exactly one sanctioned dependency; any other pip install is blocked.
PIP_INSTALL = re.compile(r"\bpip3?\s+install\b", re.I)
PIP_JPHOLIDAY = re.compile(r"\bpip3?\s+install\s+jpholiday\b", re.I)


def main() -> None:
    raw = sys.stdin.read()
    try:
        d = json.loads(raw)
    except Exception:
        _block("unparseable PreToolUse payload", "parse-error")

    tool = (d.get("tool_name") or "") if isinstance(d, dict) else ""

    if tool and FORBIDDEN_MCP.search(tool):
        _block(f"forbidden tool {tool} (pipeline is read + Notion-write only)", tool)

    if tool == "Bash":
        ti = d.get("tool_input") or {}
        cmd = ti.get("command", "") if isinstance(ti, dict) else ""
        if not isinstance(cmd, str):
            _block("invalid Bash command", "bash")
        if DANGEROUS_RE.search(cmd):
            _block("Bash contains a dangerous primitive (network / exec / dynamic-code / secret-path)", f"bash:{cmd[:80]}")
        if SHELL_DANGER.search(cmd):
            _block("Bash pipes into an interpreter or invokes a dangerous binary", f"bash:{cmd[:80]}")
        if PIP_INSTALL.search(cmd) and not PIP_JPHOLIDAY.search(cmd):
            _block("pip install of a non-sanctioned package (only jpholiday is allowed)", f"bash:{cmd[:80]}")
        _log(f"allow bash: {cmd[:100]}")
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
