#!/bin/sh
set -e

# Create directories in home (user has write access)
mkdir -p /home/node/.openclaw /home/node/workspace

# Generate gateway token if not provided
if [ -z "$OPENCLAW_GATEWAY_TOKEN" ]; then
  export OPENCLAW_GATEWAY_TOKEN=$(cat /proc/sys/kernel/random/uuid | tr -d '-')
  echo "Generated OPENCLAW_GATEWAY_TOKEN: $OPENCLAW_GATEWAY_TOKEN"
fi

# Copy and process config if it doesn't exist yet
if [ ! -f /home/node/.openclaw/config.json ]; then
  # Substitute environment variables using sed
  sed -e "s|\${OPENROUTER_API_KEY}|${OPENROUTER_API_KEY}|g" \
      -e "s|\${TELEGRAM_BOT_TOKEN}|${TELEGRAM_BOT_TOKEN}|g" \
      -e "s|\${RAILWAY_PUBLIC_DOMAIN}|${RAILWAY_PUBLIC_DOMAIN}|g" \
      -e "s|\${TELEGRAM_WEBHOOK_SECRET}|${TELEGRAM_WEBHOOK_SECRET}|g" \
      -e "s|\${SETUP_PASSWORD}|${SETUP_PASSWORD}|g" \
      -e "s|\${OPENCLAW_GATEWAY_TOKEN}|${OPENCLAW_GATEWAY_TOKEN}|g" \
      /tmp/openclaw-config.json > /home/node/.openclaw/config.json
  echo "Created config at /home/node/.openclaw/config.json"
fi

# Start OpenClaw gateway with token
exec node dist/index.js gateway --token "$OPENCLAW_GATEWAY_TOKEN"
