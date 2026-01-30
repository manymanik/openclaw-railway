FROM ghcr.io/openclaw/openclaw:latest

# Set environment variables
ENV PORT=8080
ENV OPENCLAW_STATE_DIR=/data/.openclaw
ENV OPENCLAW_WORKSPACE_DIR=/data/workspace

# Copy config to staging location (will be moved at runtime)
COPY config/config.json /tmp/openclaw-config.json
COPY entrypoint.sh /entrypoint.sh

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
