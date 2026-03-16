# TeleBot Autoreply EA (EA Budak Ubat)

An advanced, human-like automated Telegram reply bot built to run on your personal Telegram account. Designed to handle customer inquiries related to the **EA Budak Ubat** trading system using the Anthropic Claude API.

Instead of using the standard Telegram Bot API (which requires a `@bot` account), this bot works directly on your **Telegram Web K** session using Playwright. It reads the DOM, types out responses character by character, and mimics real human behavior — making it indistinguishable from a real person.

## ✨ Features

### 🤖 Core Automation
* **Human-Like Typing:** Types messages character by character with randomized delays — looks exactly like a real person typing.
* **Smart Folder Detection:** Scans only the **Personal** and **Unread** folder tabs, skipping junk and irrelevant groups.
* **Forum & Group Handling:** Detects forum-style groups (with topic subchannels) and muted chats, skipping them to avoid infinite loops.
* **Self-Chat Protection:** Automatically skips "Saved Messages" and "My Notes" to prevent replying to yourself.
* **Unreplied Chat Detection:** Finds chats from today that haven't been replied to yet, even if they don't show an unread badge.

### 🧠 AI-Powered Replies
* **Context-Aware AI:** Reads the last **30 messages** of conversation history to generate accurate, context-specific replies.
* **Natural Persona:** Replies like a real human friend — casual, empathetic, and humorous. No robotic customer-service tone.
* **Anti-Repetition:** Never repeats the same joke or phrase twice in a conversation. Each reply is fresh and relevant.
* **No Unnecessary Questions:** Doesn't end messages with filler questions like "Ada apa-apa boleh bantu?" unless clarification is actually needed.
* **Image Recognition (Vision):** Can see and understand images sent by customers — memes, forex charts, screenshots — and reply accordingly.
* **Language Matching:** Automatically replies in the same language the customer uses. BM gets BM, English gets English.

### 📋 Account Number Capture
* **Automatic Detection:** Extracts broker account numbers from conversations using regex (e.g., "xm 43195947", "akaun number saya 28430346").
* **Persistent Storage:** Saves captured accounts to `accounts.txt` with chat name, broker, account number, and timestamp.
* **Anti-Repeat Logic:** Injects known account numbers into the AI prompt so it never asks the customer for their account number again.
* **Duplicate Prevention:** Won't save the same account number twice for the same customer.

### 🛡️ Safety & Budget
* **Rate Limit Handling:** Gracefully handles Anthropic API rate limits with automatic retry.
* **Credit Protection:** Pauses all API calls for 5 minutes if the billing balance runs out, then resumes automatically.
* **Supabase Persistence (Optional):** Syncs replied message IDs and chat states to Supabase for cross-session persistence.

## 🛠️ Prerequisites
1. **Windows 10/11**
2. **Python 3.10+**
3. **Brave Browser** (installed at `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`)
4. An **Anthropic API Key** (for Claude) — get one at [console.anthropic.com](https://console.anthropic.com/)

## 🚀 Setup Instructions

### 1. Configure the API Key
1. Rename `.env.example` to `.env`.
2. Open `.env` and replace `your_api_key_here` with your Anthropic API Key.
   * Ensure your account has active billing credits (at least $5).

### 2. (Optional) Configure Supabase Persistence
Add these to your `.env` for cross-session state persistence:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Start the Browser
1. Double-click `START_BRAVE.bat`.
2. A Brave window opens with remote-debugging enabled at `http://localhost:9222`.
3. It loads `https://web.telegram.org/k/` automatically.
4. **Log in** to your Telegram account (QR code or phone number).

### 4. Start the Bot
1. Leave the Brave browser running with the Telegram tab active.
2. Double-click `START_BOT.bat`.
3. The terminal will auto-install requirements and launch the bot.
4. The bot will begin scanning your folders for new and unreplied messages.

## ⚙️ Configuration (`config.py`)

| Setting | Description | Default |
|---------|-------------|---------|
| `SCAN_FOLDERS` | Telegram folder tabs to monitor | `["Personal", "Unread"]` |
| `TYPING_SPEED` | Seconds per character for simulated typing | `0.02` |
| `MIN_REPLY_DELAY` / `MAX_REPLY_DELAY` | Human-like reading delay before responding | `3s / 8s` |
| `CHECK_INTERVAL` | Seconds between scan cycles | `15` |
| `ALLOWED_GROUP_NAMES` | Group chats the bot is allowed to reply in | See config.py |
| `GROUP_TRIGGERS` | Keywords that trigger replies in group chats | See config.py |
| `SYSTEM_PROMPT_TEMPLATE` | The AI persona and behavior rules | See config.py |

## 📁 Generated Files

| File | Description |
|------|-------------|
| `accounts.txt` | Auto-captured broker account numbers from customer chats |
| `knowledge_cache.txt` | Cached knowledge from websites and GitHub (refreshed hourly) |

## ⚠️ Limitations & Warning
* **Telegram Terms of Service:** Operating an automated script on a personal account is technically against the Telegram ToS. Use responsibly for personal business needs only. Do not use for spam.
* **Web UI Changes:** Since this uses Playwright to read the DOM, any major updates by Telegram to `web.telegram.org/k` may require updating the CSS selectors in `auto_reply.py`.

---
*Created by Syarief Azman ([@SyariefAzman](https://t.me/SyariefAzman)) — Developer of [EA Budak Ubat](https://eabudakubat.com)*
