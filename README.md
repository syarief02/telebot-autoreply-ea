# TeleBot Autoreply EA (EA Budak Ubat)

An advanced, human-like automated Telegram reply bot built to act on your personal Telegram account. It is specifically designed to handle inquiries related to the **EA Budak Ubat** trading system by leveraging Claude 3 (Anthropic API).

Instead of using the standard Telegram Bot API (which requires an `@bot` account and forces users to `/start`), this bot works directly on top of your **Telegram Web K** session using Playwright. It reads the DOM, types out responses character by character, and mimics real human behavior.

## ✨ Features
* **Human-like Automation:** Operates strictly on your personal Telegram Web session. It types out messages with randomized delays and human-like typing speeds.
* **Smart Folder Detection:** Specifically scans only the **Personal** and **Unread** folder tabs, ensuring it doesn't process junk or unnecessary groups.
* **Dynamic Forum and Group Handling:** Intelligently detects muted chats or complex forum groups (groups with topic subchannels) and skips them to avoid infinite loops and false triggers.
* **Context-Aware AI:** Uses `claude-3-haiku` to dynamically read GitHub README knowledge and generate accurate, context-specific replies in the exact language the user asked in (English or BM).
* **Automatic Chat Status Tracking:** Reads unread badges, answers questions, and clears the unread notifications without disturbing the rest of the application.
* **Rate Limits & Budget Protection:** Automatically handles Anthropic API rate limits and cleanly pauses if the credit balance runs out.

## 🛠️ Prerequisites
1. **Windows 10/11**
2. **Python 3.10+**
3. **Brave Browser** (Must be installed at `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`)
4. An **Anthropic API Key** (for Claude).

## 🚀 Setup Instructions

### 1. Configure the API Key
1. Rename the `.env.example` file to `.env`.
2. Open `.env` in Notepad and replace `your_api_key_here` with your actual Anthropic API Key.
   * *You can get a key at [console.anthropic.com](https://console.anthropic.com/). Ensure your account has active billing credits limits (at least $5).*

### 2. Start the Browser Setup
1. Double-click the `START_BRAVE.bat` file.
2. A new Brave Browser window will open with a remote-debugging port enabled at `http://localhost:9222`.
3. The browser will automatically load `https://web.telegram.org/k/`.
4. **Log in to your Telegram account** by scanning the QR code or using your phone number.

### 3. Start the Bot
1. Leave the Brave browser running with the Telegram tab active.
2. Double-click the `START_BOT.bat` file.
3. A terminal window will open, install any missing requirements automatically, and start the python script.
4. The bot will begin scanning your "Personal" and "Unread" folders for new messages.

## ⚙️ Configuration (`config.py`)
You can tweak the bot's behavior by editing `config.py`:
* `SCAN_FOLDERS`: List of Telegram folder tabs to monitor (default: `["Personal", "Unread"]`).
* `TYPING_SPEED`: Adjust the simulated typing speed in seconds per character.
* `MIN_REPLY_DELAY` / `MAX_REPLY_DELAY`: Time to wait before responding, to simulate human reading time.
* `CHECK_INTERVAL`: Re-scan loop interval.

## ⚠️ Limitations & Warning
* **Telegram Terms of Service:** Operating an automated script on a personal account is technically against the Telegram ToS. Use this tool responsibly for your personal business needs. Do not use for spam.
* **Web UI Changes:** Because this uses Playwright to read the DOM, any major updates pushed by Telegram to `web.telegram.org/k` might require updating the CSS selectors in `auto_reply.py`.

---
*Created by Syarief Azman (@SyariefAzman)*
