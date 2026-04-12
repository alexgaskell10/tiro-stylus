"""CLI entry point for tiro-stylus."""
from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

import click

_LOG_DIR = Path.home() / ".tiro-stylus" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_fmt = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_file_handler = logging.handlers.TimedRotatingFileHandler(
    _LOG_DIR / "tiro-stylus.log",
    when="midnight",
    backupCount=30,
    encoding="utf-8",
)
_file_handler.setFormatter(_fmt)
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_fmt)
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler])


def _client():
    from .telegram import TelegramClient

    token = os.environ.get("STYLUS_TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("STYLUS_TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise click.ClickException(
            "STYLUS_TELEGRAM_BOT_TOKEN and STYLUS_TELEGRAM_CHAT_ID must be set"
        )
    return TelegramClient(bot_token=token, chat_id=chat_id)


@click.group()
def cli():
    """Tiro Stylus — Telegram-triggered Claude Code assistant."""


@cli.command()
def listen():
    """Start the Telegram listener daemon."""
    from .listener import listen as _listen

    _listen(_client())


@cli.command()
@click.argument("text")
def send(text):
    """Send TEXT to Alex via Telegram. Used by Claude to reply."""
    from .history import append
    _client().send(text)
    append("tiro", text)


def main():
    cli()


if __name__ == "__main__":
    main()
