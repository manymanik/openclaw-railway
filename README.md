# OpenClaw Railway Deployment

Deploy OpenClaw AI Gateway on Railway with OpenRouter (Kimi K2.5) and Telegram integration.

## Features

- **AI Provider**: OpenRouter with Kimi K2.5 model
- **Zero Data Retention (ZDR)**: Routes only through AtlasCloud provider
- **Messaging**: Telegram bot integration
- **Privacy**: `data_collection: deny` enforced

## Quick Start

### 1. Prerequisites

- [Railway account](https://railway.app)
- [OpenRouter API key](https://openrouter.ai/keys)
- Telegram bot token (from [@BotFather](https://t.me/BotFather))

### 2. Create Telegram Bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot`
3. Choose a name and username (must end in `bot`)
4. Save the token you receive

### 3. Deploy to Railway

#### Option A: Connect GitHub Repo

1. Push this repo to your GitHub
2. In Railway, create **New Project** → **Deploy from GitHub repo**
3. Select your repository
4. Railway will auto-detect the Dockerfile

#### Option B: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### 4. Configure Environment Variables

In Railway dashboard → Your Service → **Variables**, add:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Your OpenRouter API key (`sk-or-...`) |
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `SETUP_PASSWORD` | Yes | Password for setup wizard |
| `OPENCLAW_GATEWAY_TOKEN` | No | Admin API token |
| `TELEGRAM_WEBHOOK_SECRET` | No | Webhook verification secret |

### 5. Add Persistent Volume

1. Go to your service in Railway
2. Click **Settings** → **Volumes**
3. Add volume with mount path: `/data`

### 6. Enable Public Access

1. **Settings** → **Networking**
2. Click **Generate Domain** or add custom domain
3. Note your URL: `https://your-app.up.railway.app`

### 7. Update Telegram Webhook URL

After getting your Railway domain, update the webhook in Railway variables:

```
RAILWAY_PUBLIC_DOMAIN=https://your-app.up.railway.app
```

### 8. Access Setup Wizard

Navigate to: `https://your-app.up.railway.app/setup`

Enter your `SETUP_PASSWORD` to complete configuration.

## Configuration Details

### OpenRouter ZDR Settings

```json
{
  "provider": {
    "order": ["atlas-cloud"],
    "allow_fallbacks": false,
    "zdr": true,
    "data_collection": "deny"
  }
}
```

- `zdr: true` - Only routes to Zero Data Retention endpoints
- `order: ["atlas-cloud"]` - Prioritizes AtlasCloud provider
- `allow_fallbacks: false` - Never routes to non-ZDR providers
- `data_collection: "deny"` - Excludes data-collecting providers

### Telegram DM Policies

In `config/config.json`, change `dmPolicy`:

- `"pairing"` - Requires pairing code approval (default, recommended)
- `"allowlist"` - Only specific users (add `allowFrom` array)
- `"open"` - Anyone can message (not recommended)

#### Allowlist Example

```json
{
  "channels": {
    "telegram": {
      "dmPolicy": "allowlist",
      "allowFrom": ["123456789", "@yourusername"]
    }
  }
}
```

## File Structure

```
OpenClaw-Railway/
├── Dockerfile           # Container build config
├── railway.toml         # Railway deployment config
├── config/
│   └── config.json      # OpenClaw configuration
├── .env.example         # Environment template
├── .gitignore
└── README.md
```

## Troubleshooting

### Bot not responding

1. Check Railway logs for errors
2. Verify `TELEGRAM_BOT_TOKEN` is correct
3. Ensure webhook URL matches your Railway domain
4. Check bot privacy settings with @BotFather (`/setprivacy`)

### ZDR routing errors

If AtlasCloud doesn't host Kimi K2.5, modify config to use any ZDR provider:

```json
{
  "provider": {
    "zdr": true,
    "data_collection": "deny"
  }
}
```

(Remove `order` and `allow_fallbacks` to allow any ZDR-compliant endpoint)

### Volume not persisting

Ensure volume is mounted at `/data` in Railway settings.

## Links

- [OpenClaw Docs](https://docs.openclaw.ai)
- [OpenRouter](https://openrouter.ai)
- [Kimi K2.5 on OpenRouter](https://openrouter.ai/moonshotai/kimi-k2.5)
- [AtlasCloud Provider](https://openrouter.ai/provider/atlas-cloud)
- [Railway Docs](https://docs.railway.app)
