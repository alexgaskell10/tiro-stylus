"""Main listener loop: poll Telegram, invoke Claude, relay errors."""
from __future__ import annotations

import logging

from . import history
from .runner import run_claude
from .telegram import TelegramClient

logger = logging.getLogger(__name__)


def listen(client: TelegramClient) -> None:
    # On startup: drain any pending Telegram messages into local history.
    # Messages that arrived within the last hour are still processed;
    # older ones are logged for context only.
    pending = client.drain_to_history(days=3)
    for text, is_recent in pending:
        if is_recent:
            logger.info("Processing recent pending message: %s", text[:80])
            _handle(client, text)

    for message in client.poll_messages():
        history.append("user", message)
        _handle(client, message)


def _handle(client: TelegramClient, message: str) -> None:
    client.send("Message received.")
    try:
        run_claude(message)
    except Exception as exc:
        logger.exception("Error running claude")
        client.send(f"Something went wrong running Claude: {exc}")
