# 🤖 EA Budak Ubat — Telegram Auto-Reply Bot

> AI-powered auto-reply bot for Telegram Web using Claude claude-sonnet-4-20250514 + Playwright browser automation. Replies to customers as **you** — not as a bot account.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Browser_Automation-2EAD33?logo=playwright&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_Sonnet-AI_Replies-8B5CF6?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/License-Private-red)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **AI-Powered Replies** | Uses Claude claude-sonnet-4-20250514 to generate contextual, intelligent responses |
| 🌐 **Auto-Knowledge Fetch** | Scrapes product info from [eabudakubat.com](https://eabudakubat.com) + GitHub READMEs on startup |
| 🧑 **Human-Like Typing** | Character-by-character typing with randomized speed to avoid detection |
| 🇲🇾 **Bilingual** | Replies in Bahasa Malaysia or English, matching the customer's language |
| 💬 **Private + Group Chat** | Replies to all private chats, and only the EA Budak Ubat group |
| 🔒 **Smart Filtering** | Ignores media-only messages, already-replied messages, and non-relevant group chats |
| 🛡️ **Crash-Proof** | All errors caught with exponential backoff — never crashes on network/API failures |
| ⏱️ **Knowledge Caching** | Caches fetched knowledge for 1 hour to avoid re-fetching and rate limits |

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Brave       │     │  auto_reply  │     │  Claude      │
│  Browser     │◄───►│  .py         │◄───►│  claude-sonnet-4-20250514  │
│  (Telegram   │ CDP │  (Playwright │ API │  (Anthropic) │
│   Web K)     │     │   + httpx)   │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────▼───────┐
                     │  Knowledge   │
                     │  Sources     │
                     │  (Website +  │
                     │   GitHub)    │
                     └──────────────┘
```

**How it works:**
1. On startup, fetches product knowledge from 13+ URLs (website pages + GitHub READMEs)
2. Connects to your already-running Brave browser via Chrome DevTools Protocol (CDP)
3. Finds the Telegram Web tab and starts monitoring for unread messages
4. When an unread message is found, reads it, generates an AI reply, and types it out character-by-character

---

## 📁 Project Structure

```
TeleBot Autoreply EA/
├── auto_reply.py       # Main bot — all logic in one file
├── requirements.txt    # Python dependencies
├── .env                # API key (gitignored)
├── .gitignore          # Excludes .env, cache, __pycache__
├── START_BRAVE.bat     # Launches Brave with remote debugging
├── START_BOT.bat       # Installs deps + starts bot
├── README.md           # This file
└── README.txt          # Setup guide (BM + EN)
```

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10/11**
- **Python 3.10+** — [Download](https://python.org)
- **Brave Browser** — [Download](https://brave.com)
- **Anthropic API Key** — [Get one](https://console.anthropic.com/)

### Setup (4 Steps)

```
1.  Open .env → replace "your_api_key_here" with your Anthropic API key
2.  Double-click START_BRAVE.bat → open web.telegram.org → log in
3.  Double-click START_BOT.bat → bot starts automatically
4.  Done! The bot is now monitoring and replying to unread messages.
```

### Manual Setup (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# Start Brave with debugging
"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\BraveDebugProfile"

# Open web.telegram.org in Brave, log in, then:
python auto_reply.py
```

---

## ⚙️ Configuration

All config values are at the top of `auto_reply.py`:

| Variable | Default | Description |
|---|---|---|
| `CHECK_INTERVAL` | `5` | Seconds between unread message scans |
| `MIN_REPLY_DELAY` | `3` | Minimum seconds before replying (human simulation) |
| `MAX_REPLY_DELAY` | `8` | Maximum seconds before replying |
| `TYPING_SPEED` | `0.04` | Seconds per character when typing |
| `KNOWLEDGE_CACHE_TTL` | `3600` | Cache TTL in seconds (1 hour) |
| `MAX_TOKENS_REPLY` | `500` | Max tokens for Claude reply |
| `ALLOWED_GROUP_NAMES` | `["ea budak ubat"]` | Group chats the bot is allowed to reply in |

---

## 🧑 Human Behavior Simulation

The bot implements multiple layers of human-like behavior to avoid Telegram detection:

1. **Reading delay** — Waits 3–8 seconds after opening a chat before typing (simulates reading)
2. **Character typing** — Types each character individually with `0.04s + random(0, 0.03s)` delay
3. **Pre-send pause** — Waits 0.5–1.5 seconds after finishing typing before pressing Enter
4. **Post-send cooldown** — Waits 1–3 seconds before moving to the next chat
5. **Scan pacing** — Only checks for new messages every 5 seconds

A typical 100-character reply takes **8–16 seconds** total — indistinguishable from a real person typing.

---

## 🌐 Knowledge Sources

The bot auto-fetches content from these sources on startup:

**Website Pages:**
- `eabudakubat.com` — Main page + all 6 product pages + guide

**GitHub READMEs:**
- `EA_Budak_Ubat` — MT4 version
- `EA_Budak_Ubat_MT5_Public` — MT5 version
- Optional: BracketBlitz, MathEdge-Pro, Aligator-Gozaimasu, Encik-Moku, GoldMind-AI

Content is cached to `knowledge_cache.txt` for 1 hour to avoid re-fetching.

---

## 💬 Chat Behavior

| Chat Type | Behavior |
|---|---|
| **Private chats** | Always replies to the last unread message |
| **EA Budak Ubat group** | Replies only when message contains: `ea`, `bot`, `syarief`, `broker`, `trading`, or `?` |
| **All other groups** | Silently ignored |

---

## 🔧 Troubleshooting

| Error | Solution |
|---|---|
| `Cannot connect to Brave on port 9222` | Run `START_BRAVE.bat` first |
| `Telegram Web tab not found` | Open `web.telegram.org` in Brave and log in |
| `ANTHROPIC_API_KEY not set` | Add your key to `.env` |
| `Rate limited by Anthropic` | Bot auto-waits 30s and retries |
| `No readable incoming message found` | Normal — message may be image/sticker only |

---

## 📋 Log Format

The bot prints timestamped, color-coded logs:

```
[10:45:23] [Init]   Fetching product knowledge...
[10:45:24] [Fetch]  eabudakubat.com → 3842 chars ✓
[10:45:30] [Init]   Bot is running! Monitoring for unread messages...
[10:46:05] [Scan]   Found 2 unread chats
[10:46:06] [AI]     Generating reply for: "berapa harga full version?"
[10:46:08] [Wait]   Simulating 4.2s reading time...
[10:46:12] [Sent]   Harga full version boleh tengok di https://tinyurl...
[10:46:15] [Skip]   Ignoring non-allowed group: Random Trading Group
```

---

## ⚠️ Disclaimer

> **Telegram's Terms of Service** prohibit automation on personal accounts. Use this bot at your own risk. This bot is designed for personal business auto-reply purposes and is **not** intended for spam or mass messaging. The human behavior simulation is designed to minimize detection risk but cannot guarantee it.

---

## 👨‍💻 Author

**Syarief Azman** — [@SyariefAzman](https://t.me/SyariefAzman)

- 🌐 Website: [eabudakubat.com](https://eabudakubat.com)
- 📱 WhatsApp: [+60194961568](https://wa.me/60194961568)
- 📢 Channel: [t.me/EABudakUbat](https://t.me/EABudakUbat)
