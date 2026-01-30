# Stage 1: Install wrapper dependencies in clean environment
FROM node:22-bookworm AS deps

WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev && npm cache clean --force

# Stage 2: Final image with OpenClaw + wrapper
FROM ghcr.io/openclaw/openclaw:latest

ENV PORT=8080
ENV OPENCLAW_STATE_DIR=/home/node/.openclaw
ENV OPENCLAW_WORKSPACE_DIR=/home/node/workspace

# Copy wrapper with pre-installed dependencies
COPY --from=deps /app/node_modules /app/node_modules
COPY package.json /app/package.json
COPY src/server.js /app/src/server.js

WORKDIR /app

EXPOSE 8080

CMD ["node", "src/server.js"]
