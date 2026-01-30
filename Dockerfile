FROM ghcr.io/openclaw/openclaw:latest

# Set environment variables
ENV PORT=8080
ENV OPENCLAW_STATE_DIR=/home/node/.openclaw
ENV OPENCLAW_WORKSPACE_DIR=/home/node/workspace

# Copy wrapper server
COPY package.json /app/package.json
COPY src/server.js /app/src/server.js

# Install wrapper dependencies
WORKDIR /app
RUN npm install --production

# Expose port
EXPOSE 8080

# Start wrapper server (which starts gateway internally)
CMD ["node", "src/server.js"]
