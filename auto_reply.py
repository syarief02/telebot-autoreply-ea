"""
EA Budak Ubat — Telegram Auto-Reply Bot v1.0
=============================================
Monitors Telegram Web (via Playwright) and auto-replies to customer
messages using Claude claude-sonnet-4-20250514. Runs on your own Telegram account
through Brave browser automation.

Author: Syarief Azman
"""

import asyncio
import os
import sys
import time
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import anthropic
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, BrowserContext

# ============================================================================
# SECTION: CONFIGURATION
# ============================================================================

BRAVE_PATH          = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
REMOTE_DEBUG_PORT   = 9222
CHECK_INTERVAL      = 5        # seconds between scans
MIN_REPLY_DELAY     = 3        # min seconds before replying (human simulation)
MAX_REPLY_DELAY     = 8        # max seconds before replying
TYPING_SPEED        = 0.04     # seconds per character
KNOWLEDGE_CACHE_TTL = 3600     # cache TTL in seconds (1 hour)
MAX_CHARS_PER_SOURCE = 4000   # max chars to extract per URL
MAX_TOKENS_REPLY    = 500      # max tokens for Claude reply

VERSION = "1.0.0"
CACHE_FILE = Path("knowledge_cache.txt")

# Group chat trigger keywords
GROUP_TRIGGERS = {"ea", "bot", "syarief", "broker", "trading", "?"}

# ============================================================================
# SECTION: KNOWLEDGE SOURCES
# ============================================================================

WEBSITE_URLS = [
    "https://eabudakubat.com",
    "https://eabudakubat.com/ea-budak-ubat",
    "https://eabudakubat.com/goldmind-ai",
    "https://eabudakubat.com/bracketblitz",
    "https://eabudakubat.com/mathedge-pro",
    "https://eabudakubat.com/aligator-gozaimasu",
    "https://eabudakubat.com/encik-moku",
    "https://eabudakubat.com/guide",
]

GITHUB_URLS = [
    "https://raw.githubusercontent.com/syarief02/EA_Budak_Ubat/main/README.md",
    "https://raw.githubusercontent.com/syarief02/EA_Budak_Ubat_MT5_Public/main/README.md",
    "https://github.com/syarief02/EA_Budak_Ubat/releases/latest",
    "https://github.com/syarief02/EA_Budak_Ubat_MT5_Public",
]

GITHUB_OPTIONAL_URLS = [
    "https://github.com/syarief02/BracketBlitz",
    "https://github.com/syarief02/MathEdge-Pro",
    "https://github.com/syarief02/Aligator-Gozaimasu",
    "https://github.com/syarief02/Encik-Moku",
    "https://github.com/syarief02/GoldMind-AI",
]

# ============================================================================
# SECTION: SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT_TEMPLATE = r"""You are Syarief Azman, a Malaysian pharmaceutical analyst and algorithmic forex
trader. You are the developer of EA Budak Ubat trading tools, sold at
https://eabudakubat.com. You are replying to customers and potential customers
on Telegram.

PERSONALITY & TONE:
- Professional but friendly and approachable
- Bilingual: reply in Bahasa Malaysia if the person writes in BM, English if
  they write in English. If mixed, match the dominant language.
- Concise: keep replies short and to the point. Never write essays.
- Helpful: always try to answer the question directly
- Honest: never promise profits or guarantee trading results
- Warm: use "😊" or "🤝" sparingly for a professional touch

REPLY RULES:
- Never say you are a bot or AI
- Never make up information not found in the knowledge base
- For broker questions: always direct them to register through the affiliate
  link for their chosen broker
- For technical issues you cannot solve: say
  "Boleh describe lebih detail? Saya akan cuba bantu." or
  "For detailed support, please check the guide at eabudakubat.com/guide"
- If asked about pricing: refer to https://tinyurl.com/eabubuy
- If asked for free version: refer to https://tinyurl.com/eabugetfree
- For account authorization: ask them to PM their account number after
  registering through the affiliate link
- Keep replies under 150 words unless the question genuinely requires more
- Do NOT repeat information the person already clearly knows
- Do NOT add unnecessary disclaimers on every reply

KEY FACTS TO ALWAYS KNOW:
- Latest EA version: v1.62
- Developer Telegram: @SyariefAzman
- Website: https://eabudakubat.com
- Buy full version: https://tinyurl.com/eabubuy
- Get free version: https://tinyurl.com/eabugetfree
- Supported brokers for free version: FISG, CXM, FBS, Headway, Forex4You,
  OctaFx, InstaForex, LiteForex, RoboForex, XM, Valetax
- Recommended leverage: 1:500 and above
- Minimum deposit: USD 100
- Recommended account type: Cent account (especially for beginners)
- VPS promo: https://tinyurl.com/GBVPSFX1 (code: GBVPSFX50)

BROKER AFFILIATE LINKS (use when directing customers to register):
- FISG: https://my.fisg.com/u/CTt0Rd
- CXM: https://secure.cxmys.com/links/go/5062
- FBS: https://fbs.partners?ibl=154319&ibp=588292
- Headway: https://headway.partners/user/signup?hwp=516d6b
- Forex4You: https://account.forex4you.com/en/user-registration/?affid=4hcnvz4
- OctaFx: https://my.octafxmy.net/change-partner-request/?partner=246630
- InstaForex: https://www.instaforex.com?x=KUSD
- LiteForex: https://www.litefinance.com/?uid=805161060
- RoboForex: https://my.roboforex.com/en/?a=mxyg
- XM: https://clicks.pipaffiliates.com/c?c=862266&l=en&p=1
- Valetax: https://ma.valetax.com/p/1939088

Below is the latest knowledge fetched from the official sources:
{knowledge}"""

# ============================================================================
# SECTION: GLOBAL STATE
# ============================================================================

replied_messages: set[str] = set()
KNOWLEDGE: str = ""

# ============================================================================
# SECTION: LOGGING
# ============================================================================


def log(tag: str, message: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{tag}] {message}")


# ============================================================================
# SECTION: KNOWLEDGE FETCHING
# ============================================================================


def is_cache_valid() -> bool:
    """Check if knowledge_cache.txt exists and is less than KNOWLEDGE_CACHE_TTL old."""
    if not CACHE_FILE.exists():
        return False
    mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
    return datetime.now() - mtime < timedelta(seconds=KNOWLEDGE_CACHE_TTL)


def load_cache() -> str:
    """Load knowledge from cache file."""
    return CACHE_FILE.read_text(encoding="utf-8")


def save_cache(content: str) -> None:
    """Save knowledge to cache file."""
    CACHE_FILE.write_text(content, encoding="utf-8")


def extract_website_text(html: str) -> str:
    """Extract meaningful text from a website HTML page, removing nav/footer/scripts."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove unwanted elements
    for tag in soup.find_all(["nav", "footer", "script", "style", "noscript", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Clean up excessive whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)[:MAX_CHARS_PER_SOURCE]


def extract_github_text(html: str, url: str) -> str:
    """Extract README content from a GitHub page or return raw markdown."""
    if "raw.githubusercontent.com" in url:
        return html[:MAX_CHARS_PER_SOURCE]
    soup = BeautifulSoup(html, "html.parser")
    readme = soup.find("article") or soup.find("div", {"id": "readme"})
    if readme:
        text = readme.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)[:MAX_CHARS_PER_SOURCE]


async def fetch_url(client: httpx.AsyncClient, url: str, is_github: bool = False) -> Optional[str]:
    """Fetch a single URL and return extracted text content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    try:
        resp = await client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        if is_github:
            text = extract_github_text(resp.text, url)
        else:
            text = extract_website_text(resp.text)
        log("Fetch", f"{url} → {len(text)} chars ✓")
        return text
    except httpx.HTTPStatusError as e:
        log("Fetch", f"{url} → HTTP {e.response.status_code} ✗")
        return None
    except Exception as e:
        log("Fetch", f"{url} → Failed ({type(e).__name__}: {e}) ✗")
        return None


async def fetch_all_knowledge() -> str:
    """Fetch all knowledge sources and combine into a single string."""
    global KNOWLEDGE

    if is_cache_valid():
        KNOWLEDGE = load_cache()
        log("Knowledge", f"Using cached knowledge ({len(KNOWLEDGE)} chars, < 1hr old)")
        return KNOWLEDGE

    log("Knowledge", "Fetching fresh knowledge from all sources...")
    parts: list[str] = []

    async with httpx.AsyncClient() as client:
        # Website pages
        for url in WEBSITE_URLS:
            text = await fetch_url(client, url, is_github=False)
            if text:
                parts.append(f"--- Source: {url} ---\n{text}\n")

        # GitHub (required)
        for url in GITHUB_URLS:
            text = await fetch_url(client, url, is_github=True)
            if text:
                parts.append(f"--- Source: {url} ---\n{text}\n")

        # GitHub (optional — skip gracefully)
        for url in GITHUB_OPTIONAL_URLS:
            text = await fetch_url(client, url, is_github=True)
            if text:
                parts.append(f"--- Source: {url} ---\n{text}\n")

    KNOWLEDGE = "\n".join(parts)
    save_cache(KNOWLEDGE)
    log("Knowledge", f"Fetched and cached {len(KNOWLEDGE)} total chars from {len(parts)} sources")
    return KNOWLEDGE


# ============================================================================
# SECTION: AI REPLY GENERATION
# ============================================================================


def build_system_prompt() -> str:
    """Build the full system prompt with injected knowledge."""
    return SYSTEM_PROMPT_TEMPLATE.format(knowledge=KNOWLEDGE)


async def generate_reply(message_text: str, api_key: str) -> Optional[str]:
    """Generate a reply using Claude claude-sonnet-4-20250514."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=MAX_TOKENS_REPLY,
            system=build_system_prompt(),
            messages=[
                {"role": "user", "content": message_text}
            ],
        )
        reply = response.content[0].text.strip()
        log("AI", f"Generated reply ({len(reply)} chars)")
        return reply
    except anthropic.RateLimitError:
        log("AI", "Rate limited by Anthropic. Waiting 30s...")
        await asyncio.sleep(30)
        return None
    except Exception as e:
        log("AI", f"Error generating reply: {type(e).__name__}: {e}")
        return None


# ============================================================================
# SECTION: BROWSER AUTOMATION
# ============================================================================


async def find_telegram_page(browser) -> Optional[Page]:
    """Find the Telegram Web tab in the connected browser."""
    for context in browser.contexts:
        for page in context.pages:
            if "web.telegram.org" in page.url:
                log("Browser", f"Found Telegram tab: {page.url}")
                return page
    return None


async def get_unread_chats(page: Page) -> list:
    """Find chat elements with unread message indicators."""
    # Multiple selector fallbacks for Telegram Web K
    selectors = [
        "a.chatlist-chat .unread-count",
        ".chatlist-chat .badge:not(.badge-muted)",
        "a.chatlist-chat .unread",
        ".chatlist-chat .badge-unread",
    ]
    for selector in selectors:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                log("Scan", f"Found {len(elements)} unread chats (selector: {selector})")
                # Return the parent chat elements
                result = []
                for el in elements:
                    parent = await el.evaluate_handle(
                        "el => el.closest('a.chatlist-chat') || el.closest('[data-peer-id]') || el.closest('.chatlist-chat')"
                    )
                    if parent:
                        result.append(parent)
                return result
        except Exception:
            continue
    return []


async def get_last_incoming_message(page: Page) -> tuple[Optional[str], Optional[str]]:
    """Get the last incoming message text and its unique ID."""
    # Find all message elements, filter out "is-out" (our own messages)
    selectors = [
        ".message:not(.is-out)",
        ".bubble:not(.is-out)",
        ".message-wrap:not(.is-out)",
    ]
    for selector in selectors:
        try:
            messages = await page.query_selector_all(selector)
            if not messages:
                continue
            # Get the last incoming message
            last_msg = messages[-1]
            # Extract message ID
            msg_id = await last_msg.get_attribute("data-mid") or \
                     await last_msg.get_attribute("data-message-id") or \
                     await last_msg.get_attribute("data-msg-id")
            if not msg_id:
                # Generate a fallback ID from content
                text_el = await last_msg.query_selector(
                    ".message-content .text-content, .message .text, .message-text"
                )
                text = await text_el.inner_text() if text_el else None
                if text:
                    msg_id = f"text-{hash(text)}"
                else:
                    continue
            else:
                text_el = await last_msg.query_selector(
                    ".message-content .text-content, .message .text, .message-text"
                )
                text = await text_el.inner_text() if text_el else None

            if text and text.strip():
                return text.strip(), str(msg_id)
        except Exception as e:
            log("Read", f"Selector '{selector}' failed: {e}")
            continue
    return None, None


async def is_group_chat(page: Page) -> bool:
    """Detect if the current chat is a group chat."""
    selectors = [
        ".chat-info .members-count",
        ".chat-info .group-info",
        ".profile-subtitle:has-text('members')",
        ".chat-title .group",
    ]
    for selector in selectors:
        try:
            el = await page.query_selector(selector)
            if el:
                return True
        except Exception:
            continue
    return False


def should_reply_in_group(message_text: str) -> bool:
    """Check if a group message contains trigger keywords."""
    text_lower = message_text.lower()
    return any(trigger in text_lower for trigger in GROUP_TRIGGERS)


async def type_and_send(page: Page, reply_text: str) -> bool:
    """Type the reply with human-like typing speed and send it."""
    # Find the message input box
    input_selectors = [
        ".input-message-input",
        "[contenteditable='true'].input-field-input",
        "[contenteditable='true']",
        ".composer-input",
    ]
    input_box = None
    for selector in input_selectors:
        try:
            input_box = await page.query_selector(selector)
            if input_box:
                break
        except Exception:
            continue

    if not input_box:
        log("Send", "Could not find message input box")
        return False

    try:
        await input_box.click()
        await asyncio.sleep(0.3)

        # Type character by character with randomized delays
        for char in reply_text:
            await input_box.type(char, delay=0)
            delay = TYPING_SPEED + random.uniform(0, 0.03)
            await asyncio.sleep(delay)

        # Wait a moment before sending (human simulation)
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Press Enter to send
        await page.keyboard.press("Enter")
        log("Sent", f"{reply_text[:80]}{'...' if len(reply_text) > 80 else ''}")
        return True
    except Exception as e:
        log("Send", f"Failed to type/send: {type(e).__name__}: {e}")
        return False


async def process_chat(page: Page, chat_element, api_key: str) -> None:
    """Click a chat, read the last message, generate reply, and send it."""
    try:
        # Click the chat to open it
        await chat_element.click()
        await asyncio.sleep(1.5)  # Wait for messages to load

        # Check if group chat
        group = await is_group_chat(page)

        # Read the last incoming message
        message_text, msg_id = await get_last_incoming_message(page)

        if not message_text or not msg_id:
            log("Skip", "No readable incoming message found")
            return

        # Skip if already replied
        if msg_id in replied_messages:
            log("Skip", f"Already replied to message {msg_id}")
            return

        # For group chats, check trigger keywords
        if group and not should_reply_in_group(message_text):
            log("Skip", f"Group message doesn't match triggers: {message_text[:50]}")
            replied_messages.add(msg_id)
            return

        log("AI", f'Generating reply for: "{message_text[:60]}..."')

        # Human-like delay before replying
        delay = random.uniform(MIN_REPLY_DELAY, MAX_REPLY_DELAY)
        log("Wait", f"Simulating {delay:.1f}s reading time...")
        await asyncio.sleep(delay)

        # Generate reply
        reply = await generate_reply(message_text, api_key)
        if not reply:
            log("Skip", "Failed to generate reply, skipping")
            return

        # Type and send
        success = await type_and_send(page, reply)
        if success:
            replied_messages.add(msg_id)

        # Wait before moving to next chat
        await asyncio.sleep(random.uniform(1, 3))

    except Exception as e:
        log("Error", f"Failed to process chat: {type(e).__name__}: {e}")


# ============================================================================
# SECTION: MAIN LOOP
# ============================================================================


async def main_loop(page: Page, api_key: str) -> None:
    """Main scanning loop — checks for unread chats and processes them."""
    consecutive_errors = 0
    max_consecutive_errors = 10

    while True:
        try:
            # Check if page is still connected
            try:
                await page.title()
            except Exception:
                log("Error", "Telegram tab disconnected. Attempting to reconnect...")
                await asyncio.sleep(10)
                continue

            # Scan for unread chats
            unread_chats = await get_unread_chats(page)

            if unread_chats:
                log("Info", f"Found {len(unread_chats)} unread chat(s)")
                for chat in unread_chats:
                    await process_chat(page, chat, api_key)
            else:
                pass  # Silent when no unread — avoid log spam

            consecutive_errors = 0
            await asyncio.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("Info", "Bot stopped by user (Ctrl+C)")
            break
        except Exception as e:
            consecutive_errors += 1
            log("Error", f"Main loop error ({consecutive_errors}/{max_consecutive_errors}): {e}")
            if consecutive_errors >= max_consecutive_errors:
                backoff = min(60, 5 * consecutive_errors)
                log("Error", f"Too many errors. Backing off for {backoff}s...")
                await asyncio.sleep(backoff)
                consecutive_errors = 0
            else:
                await asyncio.sleep(CHECK_INTERVAL)


# ============================================================================
# SECTION: STARTUP
# ============================================================================


def print_banner() -> None:
    """Print the startup banner."""
    print()
    print("=" * 64)
    print("  EA BUDAK UBAT — TELEGRAM AUTO-REPLY BOT")
    print(f"  Version {VERSION}")
    print("  by Syarief Azman (@SyariefAzman)")
    print("=" * 64)
    print()
    print(f"  Config:")
    print(f"    Check Interval .... {CHECK_INTERVAL}s")
    print(f"    Reply Delay ....... {MIN_REPLY_DELAY}–{MAX_REPLY_DELAY}s")
    print(f"    Typing Speed ...... {TYPING_SPEED}s/char")
    print(f"    Cache TTL ......... {KNOWLEDGE_CACHE_TTL}s")
    print(f"    Max Reply Tokens .. {MAX_TOKENS_REPLY}")
    print()


async def run() -> None:
    """Main entry point — fetch knowledge, connect to browser, start loop."""
    load_dotenv()

    # Validate API key
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        print()
        print("[ERROR] ANTHROPIC_API_KEY not set!")
        print("        1. Open .env file")
        print("        2. Replace 'your_api_key_here' with your actual key")
        print("        3. Get a key at https://console.anthropic.com/")
        print()
        sys.exit(1)

    print_banner()

    # Fetch knowledge
    log("Init", "Fetching product knowledge...")
    await fetch_all_knowledge()
    print()

    # Connect to Brave via CDP
    log("Init", f"Connecting to Brave on port {REMOTE_DEBUG_PORT}...")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{REMOTE_DEBUG_PORT}")
            log("Init", "Connected to Brave browser ✓")
        except Exception as e:
            print()
            print(f"[ERROR] Cannot connect to Brave on port {REMOTE_DEBUG_PORT}")
            print()
            print("  Make sure you:")
            print("  1. Run START_BRAVE.bat first")
            print("  2. Open https://web.telegram.org in the Brave window")
            print("  3. Log in to your Telegram account")
            print("  4. Then run this bot")
            print()
            print(f"  Technical error: {e}")
            print()
            sys.exit(1)

        # Find Telegram tab
        page = await find_telegram_page(browser)
        if not page:
            print()
            print("[ERROR] Telegram Web tab not found!")
            print()
            print("  1. Open https://web.telegram.org in your Brave browser")
            print("  2. Log in to your Telegram account")
            print("  3. Restart this bot")
            print()
            sys.exit(1)

        log("Init", "Bot is running! Monitoring for unread messages...")
        log("Init", "Press Ctrl+C to stop")
        print()

        # Start main loop
        await main_loop(page, api_key)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log("Info", "Bot stopped.")
