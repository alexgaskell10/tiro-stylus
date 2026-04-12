#!/usr/bin/env bash
# Source this file to load tiro-stylus secrets into env vars.
# Usage: source scripts/load_secrets.sh

REGION="us-east-1"

_get_secret() {
  aws secretsmanager get-secret-value \
    --secret-id "$1" \
    --region "$REGION" \
    --query 'SecretString' \
    --output text 2>/dev/null
}

export STYLUS_TELEGRAM_BOT_TOKEN=$(_get_secret tiro/telegram/stylus/bot_token)
export STYLUS_TELEGRAM_CHAT_ID=$(_get_secret tiro/telegram/chat_id)

echo "Loaded secrets: STYLUS_TELEGRAM_BOT_TOKEN STYLUS_TELEGRAM_CHAT_ID"
