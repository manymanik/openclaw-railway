#!/bin/sh
set -e

echo "Starting OpenClaw Gateway..."
echo "OPENCLAW_STATE_DIR: $OPENCLAW_STATE_DIR"

# Create directories
mkdir -p /home/node/.openclaw /home/node/workspace

# Generate gateway token if not provided
if [ -z "$OPENCLAW_GATEWAY_TOKEN" ]; then
  export OPENCLAW_GATEWAY_TOKEN=$(cat /proc/sys/kernel/random/uuid | tr -d '-')
  echo "Generated OPENCLAW_GATEWAY_TOKEN: $OPENCLAW_GATEWAY_TOKEN"
fi

# Create minimal config
cat > /home/node/.openclaw/config.json << EOF
{
  "gateway": {
    "mode": "local",
    "host": "0.0.0.0",
    "port": 8080,
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

echo "Config created:"
cat /home/node/.openclaw/config.json

# Start gateway
exec node dist/index.js gateway --allow-unconfigured --token "$OPENCLAW_GATEWAY_TOKEN"
