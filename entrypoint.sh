#!/bin/sh
set -e

# Create data directories if they don't exist (volume is mounted at runtime)
mkdir -p /data/.openclaw /data/workspace

# Copy config if it doesn't exist yet
if [ ! -f /data/.openclaw/config.json ]; then
  cp /tmp/openclaw-config.json /data/.openclaw/config.json
  echo "Copied initial config to /data/.openclaw/config.json"
fi

# Start OpenClaw gateway
exec openclaw gateway
