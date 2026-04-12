"""Telegram send/receive for tiro-stylus."""
from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

_API = "https://api.telegram.org/bot{token}/{method}"
_MAX_MSG = 4096


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._token = bot_token
        self._chat_id = str(chat_id)
        self._last_update_id: int = 0

    def send(self, text: str) -> None:
        """Send a message, chunking if over Telegram's 4096-char limit."""
        for chunk in _chunk(text, _MAX_MSG):
            self._api("sendMessage", {"chat_id": self._chat_id, "text": chunk})
            logger.info("→ sent (%d chars)", len(chunk))

    def drain_to_history(self, days: int = 3) -> list[tuple[str, bool]]:
        """Consume all pending Telegram updates and log them to local history.

        Returns a list of (text, is_recent) tuples where is_recent means the
        message arrived within the last hour and should still be processed.
        """
        from . import history

        cutoff_log = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_process = datetime.now(timezone.utc) - timedelta(hours=1)

        updates = self._get_updates(timeout=0)
        if not updates:
            return []

        results = []
        for update in updates:
            self._last_update_id = update["update_id"] + 1
            msg = update.get("message", {})
            if str(msg.get("chat", {}).get("id")) != self._chat_id:
                continue
            text = msg.get("text", "").strip()
            if not text:
                continue

            msg_ts = datetime.fromtimestamp(msg.get("date", 0), tz=timezone.utc)
            if msg_ts < cutoff_log:
                continue

            history.append("user", text)
            is_recent = msg_ts >= cutoff_process
            results.append((text, is_recent))
            logger.info("startup drain: [%s] %s (recent=%s)", msg_ts.strftime("%H:%M"), text[:60], is_recent)

        return results

    def poll_messages(self) -> Iterator[str]:
        """Yield message texts from the configured chat, forever."""
        logger.info("Polling for messages (chat_id=%s)...", self._chat_id)
        while True:
            try:
                updates = self._get_updates(timeout=30)
            except Exception as exc:
                logger.warning("Poll error: %s", exc)
                time.sleep(5)
                continue

            for update in updates:
                self._last_update_id = update["update_id"] + 1
                msg = update.get("message", {})
                if str(msg.get("chat", {}).get("id")) == self._chat_id:
                    text = msg.get("text", "").strip()
                    if text:
                        logger.info("← received: %s", text[:120])
                        yield text

    def _get_updates(self, timeout: int = 0) -> list:
        url = _API.format(token=self._token, method="getUpdates")
        resp = requests.get(
            url,
            params={
                "offset": self._last_update_id,
                "timeout": timeout,
                "allowed_updates": ["message"],
            },
            timeout=timeout + 10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            return []
        return data.get("result", [])

    def _api(self, method: str, payload: dict) -> dict:
        url = _API.format(token=self._token, method=method)
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
        return data.get("result", {})


def _chunk(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]
