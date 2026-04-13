"""Invoke claude CLI non-interactively."""
from __future__ import annotations

import logging
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Repo root — three levels up from src/tiro_stylus/runner.py
_REPO = Path(__file__).parent.parent.parent

_CONVERSATIONS_DIR = Path.home() / ".tiro-stylus" / "conversations"

_SEND = "/home/ec2-user/tiro-stylus/.venv/bin/tiro-stylus send"

_PREAMBLE = (
    "You are Tiro — Marcus Tullius Tiro — faithful secretary and freedman of Cicero, "
    "now rendered in digital form as Alex's personal AI assistant on this EC2 instance. "
    "You are learned, loyal, and precise. You speak with the measured wisdom of a Roman "
    "scholar — formal but warm, never verbose without cause. You may draw on Latin "
    "expressions or Roman sensibility where it fits naturally, but do not overdo it.\n\n"
    "You were triggered by a Telegram message from Alex (your dominus).\n\n"
    f"To communicate, run: {_SEND} \"your message\" — this is the ONLY way Alex sees your response. "
    "Do NOT output text directly. Use the send command for every reply, including short ones.\n\n"
    "IMPORTANT: Your very first action must be to send a brief message acknowledging you have "
    "received the task and are now working on it. Something in character — e.g. "
    "'I have received your words, Dominus. I shall attend to this at once.' "
    "Then proceed with the task.\n\n"
    "Message from Alex: "
)


def run_claude(message: str) -> None:
    """Spawn claude with the given message and wait for it to finish.

    Claude is responsible for sending its own replies via `tiro-stylus send`.
    The full conversation (tool calls, results, cost) is saved to a JSON file.
    """
    from . import history

    _CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

    history_ctx = history.format_for_context(days=3)
    prompt = history_ctx + _PREAMBLE + message
    cmd = [
        "claude",
        "--model", "claude-sonnet-4-6",
        "--dangerously-skip-permissions",
        "--verbose",
        "--output-format", "json",
        "-p",
        "--",
        prompt,
    ]
    logger.info("Spawning claude for: %s", message[:80])

    result = subprocess.run(
        cmd,
        cwd=_REPO,
        capture_output=True,
        text=True,
    )

    # Save full conversation transcript
    slug = message[:40].replace(" ", "_").replace("/", "-")
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = _CONVERSATIONS_DIR / f"{ts}_{slug}.json"
    log_path.write_text(result.stdout, encoding="utf-8")
    logger.info("Conversation saved: %s", log_path)

    if result.stderr.strip():
        logger.warning("claude stderr:\n%s", result.stderr)
    if result.returncode != 0:
        logger.error("claude exited with code %d", result.returncode)
        raise RuntimeError(f"claude exited with code {result.returncode}")
