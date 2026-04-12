"""Local conversation history store."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_HISTORY_FILE = Path.home() / ".tiro-stylus" / "history.jsonl"


def append(role: str, text: str) -> None:
    """Append a message to the history file."""
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "text": text,
    }
    with _HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def recent(days: int = 3) -> list[dict]:
    """Return entries from the last N days, oldest first."""
    if not _HISTORY_FILE.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries = []
    with _HISTORY_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["ts"])
                if ts >= cutoff:
                    entries.append(entry)
            except Exception:
                pass
    return entries


def format_for_context(days: int = 3) -> str:
    """Return recent history as a human-readable block for Claude's preamble."""
    entries = recent(days)
    if not entries:
        return ""

    lines = []
    for e in entries:
        ts = datetime.fromisoformat(e["ts"]).strftime("%Y-%m-%d %H:%M")
        role = "Alex" if e["role"] == "user" else "tiro"
        lines.append(f"[{ts}] {role}: {e['text']}")

    return "--- Recent conversation (last 3 days) ---\n" + "\n".join(lines) + "\n--- End of history ---\n\n"
