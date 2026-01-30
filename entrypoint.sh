#!/bin/sh
set -e

echo "Starting OpenClaw Gateway..."

# Clean old configs to start fresh
rm -rf /home/node/.openclaw/*
rm -rf /home/node/.config/openclaw 2>/dev/null || true

# Create directories
mkdir -p /home/node/.openclaw /home/node/workspace

# Generate gateway token if not provided
if [ -z "$OPENCLAW_GATEWAY_TOKEN" ]; then
  export OPENCLAW_GATEWAY_TOKEN=$(cat /proc/sys/kernel/random/uuid | tr -d '-')
  echo "Generated OPENCLAW_GATEWAY_TOKEN: $OPENCLAW_GATEWAY_TOKEN"
fi

# Use Railway's PORT or default to 8080
export OPENCLAW_GATEWAY_PORT="${PORT:-8080}"
export OPENCLAW_GATEWAY_HOST="0.0.0.0"

# Create config with correct port
cat > /home/node/.openclaw/config.json << EOF
{
  "gateway": {
    "mode": "local",
    "host": "0.0.0.0",
    "port": ${OPENCLAW_GATEWAY_PORT},
    "network": "lan",
    "auth": {
      "token": "$OPENCLAW_GATEWAY_TOKEN"
    }
  },
  "models": {
    "default": "openrouter/moonshotai/kimi-k2.5",
    "providers": {
      "openrouter": {
        "apiKey": "$OPENROUTER_API_KEY"
      }
    }
  }
}
EOF

echo "Config created with port ${OPENCLAW_GATEWAY_PORT}:"
cat /home/node/.openclaw/config.json

# Start gateway
exec node dist/index.js gateway \
  --allow-unconfigured \
  --token "$OPENCLAW_GATEWAY_TOKEN" \
  --port "$OPENCLAW_GATEWAY_PORT"
