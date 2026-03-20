"""
Claude Code Stop hook — token usage tracker.

Reads JSON from stdin (Claude Code Stop event), extracts token counts,
git user, and active feature from HOT.md, then appends one JSONL record
to .claude/logs/token-usage.jsonl.

Contract: always exits 0. Never raises. Never blocks Claude workflow.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# repo_root: .claude/scripts/ → .claude/ → project root
REPO_ROOT = Path(__file__).parent.parent.parent
HOT_MD = REPO_ROOT / ".claude" / "memory" / "HOT.md"
LOG_DIR = REPO_ROOT / ".claude" / "logs"
LOG_FILE = LOG_DIR / "token-usage.jsonl"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def parse_stdin() -> dict:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def parse_last_assistant_turn(transcript_path: str) -> dict:
    """
    Read transcript JSONL, return token usage from the last assistant entry.
    Returns dict with token counts + model, or zeros if not found.
    """
    last_usage: dict = {}
    last_model = "unknown"
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if entry.get("type") == "assistant":
                    msg = entry.get("message") or {}
                    usage = msg.get("usage")
                    if usage:
                        last_usage = usage
                        last_model = msg.get("model") or last_model
    except Exception:
        pass
    return {
        "input_tokens": int(last_usage.get("input_tokens") or 0),
        "output_tokens": int(last_usage.get("output_tokens") or 0),
        "cache_read_tokens": int(last_usage.get("cache_read_input_tokens") or 0),
        "cache_write_tokens": int(last_usage.get("cache_creation_input_tokens") or 0),
        "model": last_model,
    }


def get_usage_and_model(data: dict) -> tuple[dict, str]:
    """Extract token counts and model. Reads from transcript if available."""
    transcript_path = data.get("transcript_path")
    if transcript_path:
        result = parse_last_assistant_turn(transcript_path)
        model = result.pop("model", "unknown")
        return result, model
    # Fallback: direct payload (forward-compat)
    usage = data.get("usage") or data.get("message", {}).get("usage") or {}
    model = (
        data.get("model")
        or data.get("claude_model")
        or (data.get("message") or {}).get("model")
        or os.environ.get("ANTHROPIC_MODEL")
        or os.environ.get("CLAUDE_MODEL")
        or "unknown"
    )
    return {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "cache_read_tokens": int(usage.get("cache_read_input_tokens") or 0),
        "cache_write_tokens": int(usage.get("cache_creation_input_tokens") or 0),
    }, model


def get_session_id(data: dict) -> str:
    try:
        return str(
            data.get("session_id")
            or data.get("sessionId")
            or ""
        )
    except Exception:
        return ""


def get_stop_reason(data: dict) -> str | None:
    try:
        return (
            data.get("stop_reason")
            or (data.get("message") or {}).get("stop_reason")
        )
    except Exception:
        return None


def git_config(field: str) -> str:
    try:
        result = subprocess.run(
            ["git", "config", field],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=str(REPO_ROOT),
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def extract_feature_from_hot(hot_path: Path) -> str:
    """
    Parse HOT.md "## In Progress" section.
    Returns: story name | "none" | "unknown"
    """
    try:
        content = hot_path.read_text(encoding="utf-8")

        section_match = re.search(
            r"## In Progress[^\n]*\n([\s\S]*)(?=\n##)",
            content,
        )
        if not section_match:
            return "none"

        for line in section_match.group(1).splitlines():
            # Match unchecked checkbox: - [ ] story-name
            match = re.match(r"\s*-\s+\[\s\]\s+([A-Za-z0-9][A-Za-z0-9_-]*)", line)
            if match:
                name = match.group(1)
                # Skip placeholder lines like "Story:" prefix
                if name.lower() not in ("story", "_none"):
                    return name
        return "none"
    except Exception:
        return "unknown"


def now_iso() -> str:
    try:
        return datetime.now().astimezone().isoformat(timespec="microseconds")
    except Exception:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def rotate_if_needed(log_path: Path) -> None:
    try:
        if log_path.exists() and log_path.stat().st_size > LOG_MAX_BYTES:
            backup = log_path.with_suffix(".jsonl.bak")
            log_path.replace(backup)
    except Exception:
        pass


def main() -> None:
    data = parse_stdin()

    usage, model = get_usage_and_model(data)
    session_id = get_session_id(data)
    stop_reason = get_stop_reason(data)

    git_user_name = git_config("user.name")
    git_user_email = git_config("user.email")
    feature = extract_feature_from_hot(HOT_MD)

    record = {
        "timestamp": now_iso(),
        "session_id": session_id,
        "git_user_name": git_user_name,
        "git_user_email": git_user_email,
        "feature": feature,
        "model": model,
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "cache_read_tokens": usage["cache_read_tokens"],
        "cache_write_tokens": usage["cache_write_tokens"],
        "stop_reason": stop_reason,
        "hook_type": "Stop",
    }

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        rotate_if_needed(LOG_FILE)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # silent — never block Claude


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
