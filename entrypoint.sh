#!/bin/sh
set -e

# Create directories in home (user has write access)
mkdir -p /home/node/.openclaw /home/node/workspace

# Copy config if it doesn't exist yet
if [ ! -f /home/node/.openclaw/config.json ]; then
  cp /tmp/openclaw-config.json /home/node/.openclaw/config.json
  echo "Copied initial config to /home/node/.openclaw/config.json"
fi

# Start OpenClaw gateway
exec node dist/index.js gateway --allow-unconfigured
