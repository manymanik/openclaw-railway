FROM ghcr.io/openclaw/openclaw:latest

# Set environment variables
ENV PORT=8080
ENV OPENCLAW_STATE_DIR=/home/node/.openclaw
ENV OPENCLAW_WORKSPACE_DIR=/home/node/workspace

# Copy entrypoint
COPY --chmod=755 entrypoint.sh /entrypoint.sh

# Expose port
EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
