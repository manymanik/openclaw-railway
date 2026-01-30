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

# Create config
cat > /home/node/.openclaw/config.json << EOF
{
  "gateway": {
    "mode": "local",
    "host": "0.0.0.0",
    "port": 18789,
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

echo "Config created"

# Start socat to forward external port to localhost
socat TCP-LISTEN:${OPENCLAW_GATEWAY_PORT},fork,reuseaddr TCP:127.0.0.1:18789 &
echo "Port forwarder started: 0.0.0.0:${OPENCLAW_GATEWAY_PORT} -> 127.0.0.1:18789"

# Start gateway on its default internal port
exec node dist/index.js gateway \
  --allow-unconfigured \
  --token "$OPENCLAW_GATEWAY_TOKEN"
