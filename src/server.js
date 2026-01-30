import express from "express";
import httpProxy from "http-proxy";
import { spawn } from "child_process";
import { existsSync, mkdirSync, writeFileSync } from "fs";
import { randomUUID } from "crypto";

// Configuration
const PORT = parseInt(process.env.PORT ?? "8080", 10);
const INTERNAL_PORT = 18789;
const GATEWAY_TARGET = `http://127.0.0.1:${INTERNAL_PORT}`;
const STATE_DIR = process.env.OPENCLAW_STATE_DIR ?? "/home/node/.openclaw";
const CONFIG_PATH = `${STATE_DIR}/config.json`;

// Gateway token
const GATEWAY_TOKEN = process.env.OPENCLAW_GATEWAY_TOKEN ?? randomUUID().replace(/-/g, "");

let gatewayProcess = null;
let gatewayReady = false;

// Create config
function createConfig() {
  mkdirSync(STATE_DIR, { recursive: true });

  const config = {
    gateway: {
      mode: "local",
      auth: {
        token: GATEWAY_TOKEN
      }
    },
    models: {
      default: "openrouter/moonshotai/kimi-k2.5",
      providers: {
        openrouter: {
          apiKey: process.env.OPENROUTER_API_KEY
        }
      }
    }
  };

  writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
  console.log(`Config created at ${CONFIG_PATH}`);
}

// Start the OpenClaw gateway
async function startGateway() {
  if (gatewayProcess) return;

  console.log("Starting OpenClaw gateway...");

  const args = [
    "dist/index.js",
    "gateway",
    "--bind", "loopback",
    "--port", String(INTERNAL_PORT),
    "--token", GATEWAY_TOKEN,
    "--allow-unconfigured"
  ];

  gatewayProcess = spawn("node", args, {
    stdio: ["ignore", "pipe", "pipe"],
    env: {
      ...process.env,
      OPENCLAW_STATE_DIR: STATE_DIR
    }
  });

  gatewayProcess.stdout.on("data", (data) => {
    const msg = data.toString();
    console.log(`[gateway] ${msg}`);
    if (msg.includes("listening on")) {
      gatewayReady = true;
    }
  });

  gatewayProcess.stderr.on("data", (data) => {
    console.error(`[gateway] ${data.toString()}`);
  });

  gatewayProcess.on("exit", (code) => {
    console.log(`Gateway exited with code ${code}`);
    gatewayProcess = null;
    gatewayReady = false;
  });

  // Wait for gateway to be ready
  await new Promise((resolve) => {
    const check = setInterval(() => {
      if (gatewayReady) {
        clearInterval(check);
        resolve();
      }
    }, 100);
    // Timeout after 30s
    setTimeout(() => {
      clearInterval(check);
      resolve();
    }, 30000);
  });
}

// Create Express app
const app = express();

// Create proxy
const proxy = httpProxy.createProxyServer({
  target: GATEWAY_TARGET,
  ws: true,
  xfwd: true
});

proxy.on("error", (err, req, res) => {
  console.error("Proxy error:", err.message);
  if (res.writeHead) {
    res.writeHead(502, { "Content-Type": "text/plain" });
    res.end("Gateway unavailable");
  }
});

// Health check
app.get("/health", (req, res) => {
  res.json({ status: gatewayReady ? "ok" : "starting", token: GATEWAY_TOKEN });
});

// Proxy all other requests
app.use(async (req, res) => {
  if (!gatewayReady) {
    await startGateway();
  }
  proxy.web(req, res);
});

// Handle WebSocket upgrades
const server = app.listen(PORT, "0.0.0.0", () => {
  console.log(`Wrapper server listening on 0.0.0.0:${PORT}`);
  console.log(`Proxying to gateway at ${GATEWAY_TARGET}`);
  console.log(`Gateway token: ${GATEWAY_TOKEN}`);

  // Create config and start gateway
  createConfig();
  startGateway();
});

server.on("upgrade", async (req, socket, head) => {
  if (!gatewayReady) {
    await startGateway();
  }
  proxy.ws(req, socket, head);
});

// Graceful shutdown
process.on("SIGTERM", () => {
  console.log("Shutting down...");
  if (gatewayProcess) {
    gatewayProcess.kill();
  }
  server.close();
  process.exit(0);
});
