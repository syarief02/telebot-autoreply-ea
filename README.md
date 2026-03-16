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
| ⚙️ **Modular Config** | All settings, URLs, and prompts live in `config.py` — easy to edit without touching bot logic |

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
                    ┌───────▼───────┐
                    │  config.py    │
                    │  (URLs, keys, │
                    │   prompt,     │
                    │   settings)   │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  Knowledge    │
                    │  Sources      │
                    │  (Website +   │
                    │   GitHub)     │
                    └───────────────┘
```

**How it works:**
1. On startup, reads config from `config.py` and fetches product knowledge from 13+ URLs
2. Connects to your already-running Brave browser via Chrome DevTools Protocol (CDP)
3. Finds the Telegram Web tab and starts monitoring for unread messages
4. When an unread message is found, reads it, generates an AI reply, and types it out character-by-character

---

## 📁 Project Structure

```
TeleBot Autoreply EA/
├── auto_reply.py       # Main bot logic (don't need to edit)
├── config.py           # ⚙️ ALL editable config — URLs, prompt, settings
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

## ⚙️ Configuration (`config.py`)

All settings are in `config.py` — you never need to edit `auto_reply.py`.

### Bot Settings

| Variable | Default | Description |
|---|---|---|
| `CHECK_INTERVAL` | `5` | Seconds between unread message scans |
| `MIN_REPLY_DELAY` | `3` | Minimum seconds before replying (human simulation) |
| `MAX_REPLY_DELAY` | `8` | Maximum seconds before replying |
| `TYPING_SPEED` | `0.04` | Seconds per character when typing |
| `KNOWLEDGE_CACHE_TTL` | `3600` | Cache TTL in seconds (1 hour) |
| `MAX_TOKENS_REPLY` | `500` | Max tokens for Claude reply |

### Chat Filter

| Variable | Default | Description |
|---|---|---|
| `ALLOWED_GROUP_NAMES` | `["ea budak ubat"]` | Group chats the bot is allowed to reply in |
| `GROUP_TRIGGERS` | `{"ea", "bot", ...}` | Keywords that trigger a reply in allowed groups |

### Adding a New EA

When you create a new EA, just add it to `config.py`:

```python
# 1. Add the website page
WEBSITE_URLS = [
    ...
    "https://eabudakubat.com/your-new-ea",       # ← add here
]

# 2. Add the GitHub repo (optional section — won't crash if 404)
GITHUB_OPTIONAL_URLS = [
    ...
    "https://github.com/syarief02/Your-New-EA",  # ← add here
]

# 3. Update KEY FACTS in SYSTEM_PROMPT_TEMPLATE if needed
```

Delete `knowledge_cache.txt` after editing to force a fresh fetch on next startup.

---

## 🧑 Human Behavior Simulation

The bot implements multiple layers of human-like behavior to avoid Telegram detection:

| Layer | Behavior | Timing |
|---|---|---|
| 📖 Reading delay | Waits before typing after opening a chat | 3–8 seconds (random) |
| ⌨️ Character typing | Types each char individually, not paste | 0.04s + random(0, 0.03s) per char |
| ⏸️ Pre-send pause | Waits after finishing typing before Enter | 0.5–1.5 seconds (random) |
| 💤 Post-send cooldown | Waits before moving to next chat | 1–3 seconds (random) |
| 🔄 Scan pacing | Checks for new messages periodically | Every 5 seconds |

**Example:** A 100-character reply takes ~8–16 seconds total — indistinguishable from a real person.

---

## 🌐 Knowledge Sources

The bot auto-fetches content from these sources on startup (all configurable in `config.py`):

**Website Pages (8 URLs):**
- Main page + all 6 product detail pages + guide page

**GitHub READMEs (4 required + 5 optional):**
- EA Budak Ubat MT4 & MT5, BracketBlitz, MathEdge Pro, Aligator Gozaimasu, Encik Moku, GoldMind AI

Content is cached to `knowledge_cache.txt` for 1 hour. Delete the cache file to force a re-fetch.

---

## 💬 Chat Behavior

| Chat Type | Behavior |
|---|---|
| **Private chats** | Always replies to the last unread message |
| **EA Budak Ubat group** | Replies only when message contains: `ea`, `bot`, `syarief`, `broker`, `trading`, or `?` |
| **All other groups** | Silently ignored (logged as `"Ignoring non-allowed group"`) |

To add more allowed groups, edit `ALLOWED_GROUP_NAMES` in `config.py`.

---

## 🔧 Troubleshooting

| Error | Solution |
|---|---|
| `Cannot connect to Brave on port 9222` | Run `START_BRAVE.bat` first |
| `Telegram Web tab not found` | Open `web.telegram.org` in Brave and log in |
| `ANTHROPIC_API_KEY not set` | Add your key to `.env` |
| `Rate limited by Anthropic` | Bot auto-waits 30s and retries |
| `No readable incoming message found` | Normal — message may be image/sticker only |
| Bot not replying to a new EA | Add the EA's URLs to `config.py` and delete `knowledge_cache.txt` |

---

## 📋 Log Format

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
