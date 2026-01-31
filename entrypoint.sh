#!/bin/bash
set -e

# Create workspace skills directory
SKILLS_DIR="${HOME}/.openclaw/workspace/skills"
mkdir -p "$SKILLS_DIR"

# Copy bundled skills if they exist
if [ -d "/app/skills" ]; then
  cp -r /app/skills/* "$SKILLS_DIR/" 2>/dev/null || true
  echo "[entrypoint] Copied skills to $SKILLS_DIR"
fi

# Run the main server
exec node src/server.js
