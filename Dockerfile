FROM ghcr.io/openclaw/openclaw:latest

# Set environment variables - use home directory paths
ENV PORT=8080
ENV OPENCLAW_STATE_DIR=/home/node/.openclaw
ENV OPENCLAW_WORKSPACE_DIR=/home/node/workspace

# Copy config to staging location
COPY config/config.json /tmp/openclaw-config.json
COPY --chmod=755 entrypoint.sh /entrypoint.sh

# Expose port
EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
