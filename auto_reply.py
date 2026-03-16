"""
EA Budak Ubat — Telegram Auto-Reply Bot v1.0
=============================================
Monitors Telegram Web (via Playwright) and auto-replies to customer
messages using Claude claude-sonnet-4-20250514. Runs on your own Telegram account
through Brave browser automation.

Author: Syarief Azman

NOTE: All editable config (URLs, system prompt, allowed groups, settings)
lives in config.py — edit that file to add new EAs or change behavior.
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
from supabase import create_client, Client

# Import all config from config.py
from config import (
    BRAVE_PATH, REMOTE_DEBUG_PORT,
    CHECK_INTERVAL, MIN_REPLY_DELAY, MAX_REPLY_DELAY,
    TYPING_SPEED, KNOWLEDGE_CACHE_TTL, MAX_CHARS_PER_SOURCE, MAX_TOKENS_REPLY,
    ALLOWED_GROUP_NAMES, GROUP_TRIGGERS,
    WEBSITE_URLS, GITHUB_URLS, GITHUB_OPTIONAL_URLS,
    SYSTEM_PROMPT_TEMPLATE, SCAN_FOLDERS,
)

VERSION = "1.1.0"
CACHE_FILE = Path("knowledge_cache.txt")

# ============================================================================
# SECTION: GLOBAL STATE
# ============================================================================

replied_messages: set[str] = set()
KNOWLEDGE: str = ""
credit_paused_until: float = 0  # Timestamp until which we pause API calls
PROCESSED_CHAT_STATES: dict[str, str] = {}  # Tracks last seen chat preview to avoid infinite loops

supabase_client: Optional[Client] = None

def init_supabase():
    global supabase_client, replied_messages, PROCESSED_CHAT_STATES
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if url and key:
        try:
            supabase_client = create_client(url, key)
            log("Supabase", "Connected to Supabase")
            # Load initial state
            try:
                msg_resp = supabase_client.table('replied_messages').select('message_id').execute()
                for row in msg_resp.data:
                    replied_messages.add(row['message_id'])
                
                state_resp = supabase_client.table('processed_chat_states').select('*').execute()
                for row in state_resp.data:
                    PROCESSED_CHAT_STATES[row['chat_name']] = row['subtitle']
                log("Supabase", f"Loaded {len(replied_messages)} messages and {len(PROCESSED_CHAT_STATES)} chat states")
            except Exception as e:
                log("Supabase", f"Error loading data (tables might not exist): {e}")
        except Exception as e:
            log("Supabase", f"Initialization failed: {e}")
            supabase_client = None
    else:
        log("Supabase", "No SUPABASE_URL or SUPABASE_KEY found. Using memory-only state.")

def save_replied_message(msg_id: str):
    replied_messages.add(msg_id)
    if supabase_client:
        try:
            supabase_client.table('replied_messages').upsert({'message_id': msg_id}).execute()
        except Exception:
            pass

def save_chat_state(chat_name: str, subtitle: str):
    PROCESSED_CHAT_STATES[chat_name] = subtitle
    if supabase_client:
        try:
            supabase_client.table('processed_chat_states').upsert({'chat_name': chat_name, 'subtitle': subtitle}).execute()
        except Exception:
            pass

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


async def generate_reply(message_text: str, api_key: str, base64_image: Optional[str] = None) -> Optional[str]:
    """Generate a reply using Claude claude-3-5-sonnet-20241022.
    Optionally includes an image for vision processing.
    Returns reply text, None on failure, or 'CREDIT_ERROR' on billing issues.
    """
    global credit_paused_until

    # If we're in credit pause mode, don't even try
    if time.time() < credit_paused_until:
        remaining = int(credit_paused_until - time.time())
        log("AI", f"Credit pause active. Waiting {remaining}s before retrying API...")
        return "CREDIT_ERROR"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Build the dynamic payload
        content_items = []
        if base64_image and base64_image.startswith("data:image"):
            # Format: 'data:image/jpeg;base64,/9j/4AAQSkZJRg...'
            try:
                media_type = base64_image.split(';')[0].split(':')[1]
                data = base64_image.split(',')[1]
                content_items.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data,
                    }
                })
                log("AI", f"Attached image payload to prompt ({len(data)} bytes, {media_type})")
            except Exception as e:
                log("AI", f"Failed to parse base64 image: {e}")
        
        content_items.append({
            "type": "text", 
            "text": message_text
        })
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=MAX_TOKENS_REPLY,
            system=build_system_prompt(),
            messages=[
                {"role": "user", "content": content_items}
            ],
        )
        reply = response.content[0].text.strip()
        log("AI", f"Generated reply ({len(reply)} chars)")
        return reply
    except anthropic.RateLimitError:
        log("AI", "Rate limited by Anthropic. Waiting 30s...")
        await asyncio.sleep(30)
        return None
    except anthropic.BadRequestError as e:
        error_msg = str(e)
        if "credit" in error_msg.lower() or "balance" in error_msg.lower() or "billing" in error_msg.lower():
            # Credit/billing error — pause ALL API calls for 5 minutes
            credit_paused_until = time.time() + 300
            log("AI", "⚠️ CREDIT ERROR: Your Anthropic credit balance is too low.")
            log("AI", "   Pausing API calls for 5 minutes. Top up at platform.claude.com/settings/billing")
            log("AI", "   The bot will keep scanning but won't make API calls until the pause ends.")
            return "CREDIT_ERROR"
        else:
            log("AI", f"Error generating reply: {type(e).__name__}: {e}")
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


async def get_unread_chats(page: Page) -> list[tuple]:
    """Find chat elements that have unread messages OR are unreplied today.
    Returns list of (element, chat_name, subtitle) tuples.
    """
    try:
        # Use a JS evaluator to find all candidate chats directly in the browser
        candidate_handles = await page.evaluate_handle('''() => {
            const chats = document.querySelectorAll('.chatlist-chat');
            const results = [];
            for (const chat of chats) {
                // 1. Check for unread badge
                const badge = chat.querySelector('.badge:not(.badge-muted), .unread, .dialog-subtitle-badge-unread');
                if (badge) {
                    results.push(chat);
                    continue;
                }
                
                // 2. Not unread. Check if it's from today and unreplied.
                const timeEl = chat.querySelector('.message-time');
                const timeText = timeEl ? timeEl.textContent.trim() : "";
                
                // If time has a colon (e.g. "10:42 AM", "18:40"), it generally means today.
                if (timeText.includes(':')) {
                    // Check if the message is from us (outgoing) by looking for visible checkmarks.
                    // Telegram Web K has a .message-status icon. If it lacks .hide, it's outgoing.
                    const outgoingStatus = chat.querySelector('.message-status:not(.hide)');
                    
                    // Also check if it's a Draft 
                    const isDraft = chat.querySelector('.dialog-subtitle .danger, .dialog-subtitle .i18n')?.textContent.includes('Draft');
                    
                    // We only want to reply if there is NO outgoing status icon and it's not a draft
                    if (!outgoingStatus && !isDraft) {
                        results.push(chat);
                    }
                }
            }
            return results;
        }''')
        
        # Process the candidates into Python objects
        length = await candidate_handles.evaluate("els => els.length")
        result = []
        for i in range(length):
            chat_el = await candidate_handles.evaluate_handle(f"els => els[{i}]")
            
            chat_name, subtitle = await chat_el.evaluate('''el => {
                const titleEl = el.querySelector('.peer-title') || el.querySelector('.user-title') || el.querySelector('.dialog-title');
                const name = titleEl ? titleEl.textContent.trim() : '';
                
                const subEl = el.querySelector('.dialog-subtitle');
                // Clean up subtitle (remove HTML elements like imgs/spans to get text)
                const sub = subEl ? subEl.innerText || subEl.textContent.trim() : '';
                
                return [name, sub];
            }''')
            
            if chat_name:
                # If we've already processed this exact message state today, skip it
                if PROCESSED_CHAT_STATES.get(chat_name) == subtitle:
                    continue
                result.append((chat_el, chat_name, subtitle))
                
        return result
        
    except Exception as e:
        log("Scan", f"Error scanning chats: {e}")
        return []


async def get_last_incoming_message(page: Page) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Get the recent chat history and the unique ID of the last incoming message."""
    try:
        # Evaluate JS to grab the last 15 messages (both incoming and outgoing)
        result = await page.evaluate('''() => {
            const messageNodes = document.querySelectorAll('.message, .bubble, .message-list-item');
            if (!messageNodes || messageNodes.length === 0) return null;
            
            let history = [];
            let lastIncomingId = null;
            
            // Only care about the last 15 messages for context
            const recentNodes = Array.from(messageNodes).slice(-15);
            
            for (const node of recentNodes) {
                const isOut = node.classList.contains('is-out') || node.classList.contains('message-out');
                const isIn = node.classList.contains('is-in') || node.classList.contains('message-in') || node.matches(':not(.is-out):not(.message-out)');
                
                // Need text or image content to continue
                const textNode = node.querySelector('.translatable-message, .text-content');
                const imgNode = node.querySelector('img.media-photo');
                
                if (!textNode && !imgNode) continue;
                
                let text = textNode ? (textNode.innerText || textNode.textContent) : "";
                
                // If it's an image and incoming, track the src
                let imgSrc = null;
                if (!isOut && imgNode && imgNode.src && imgNode.src.startsWith('blob:')) {
                    imgSrc = imgNode.src;
                }
                if (text && text.trim()) {
                    text = text.trim();
                    const sender = isOut ? "You" : "Customer";
                    history.push(`${sender}: ${text}`);
                } else if (imgSrc) {
                    const sender = "Customer";
                    history.push(`${sender}: [Sent an image]`);
                }
                
                if (!isOut) {
                    lastIncomingId = node.getAttribute('data-mid') || node.getAttribute('data-message-id') || `msg-${Math.random()}`;
                    if (imgSrc) {
                        lastIncomingId += `|img|${imgSrc}`; // Attach image src to ID for extraction
                    }
                }
            }
            
            if (history.length === 0) return null;
            
            return {
                historyText: history.join('\\n'),
                lastId: lastIncomingId
            };
        }''')
        
        if result and result.get("historyText") and result.get("lastId"):
            history_text = result["historyText"]
            last_id = str(result["lastId"])
            
            # Check if there's an image to extract from the last incoming message
            base64_img = None
            if "|img|" in last_id:
                parts = last_id.split("|img|", 1)
                last_id = parts[0]
                blob_url = parts[1]
                
                log("Read", f"Found image in message ({blob_url}). Extracting Base64...")
                
                # We need to fetch the blob natively using page.evaluate
                base64_img = await page.evaluate(f'''async (blobUrl) => {{
                    try {{
                        const response = await fetch(blobUrl);
                        const blob = await response.blob();
                        return new Promise((resolve, reject) => {{
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.onerror = reject;
                            reader.readAsDataURL(blob);
                        }});
                    }} catch (e) {{
                        return null;
                    }}
                }}''', blob_url)
                
            return history_text, last_id, base64_img
            
    except Exception as e:
        log("Read", f"Failed to extract chat history: {e}")
        
    return None, None, None


async def get_chat_title(page: Page) -> str:
    """Get the title/name of the currently open chat."""
    selectors = [
        ".chat-info .peer-title",
        ".top .peer-title",
        ".chat-info-container .peer-title",
    ]
    for selector in selectors:
        try:
            el = await page.query_selector(selector)
            if el:
                title = await el.inner_text()
                if title and title.strip():
                    return title.strip()
        except Exception:
            continue
    return ""


async def is_group_chat(page: Page) -> bool:
    """Detect if the current chat is a group/channel (not a private chat).
    Checks the chat header subtitle for 'member' keyword.
    """
    try:
        # Telegram Web K shows "X members, Y online" in the subtitle for groups
        result = await page.evaluate("""() => {
            const subtitle = document.querySelector('.chat-info .info .subtitle, .chat-info .info, .chat-info .subtitle');
            if (subtitle) {
                const text = subtitle.textContent.toLowerCase();
                return text.includes('member') || text.includes('subscriber');
            }
            return false;
        }""")
        return bool(result)
    except Exception:
        pass
    # Fallback: check for known group indicators
    selectors = [
        ".chat-info .members-count",
        ".chat-info .group-info",
    ]
    for selector in selectors:
        try:
            el = await page.query_selector(selector)
            if el:
                return True
        except Exception:
            continue
    return False


def is_allowed_group(chat_title: str) -> bool:
    """Check if the group name matches one of the allowed groups."""
    title_lower = chat_title.lower()
    return any(name in title_lower for name in ALLOWED_GROUP_NAMES)


def is_private_chat(chat_name: str) -> bool:
    """Heuristic: if a chat name doesn't match any known group pattern, treat as private."""
    # This is a best-effort check from the chatlist sidebar
    return True  # Will be verified after clicking via is_group_chat()


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


async def process_chat(page: Page, chat_element, chat_name: str, api_key: str) -> None:
    """Process an unread chat: pre-filter by name, click, read, reply."""
    try:
        # === PRE-FILTER: Check chat name BEFORE clicking ===
        # If we got a name from the chatlist and it looks like a non-allowed group,
        # skip it immediately without wasting time clicking into it
        if chat_name and not is_allowed_group(chat_name):
            # Could be a private chat or a non-allowed group.
            # We do a quick heuristic: names with many words or special chars = likely group
            # But to be safe, we'll still click into private-looking chats
            # Only skip if it clearly looks like a group name (long, has keywords)
            pass  # Can't reliably tell from name alone, proceed to click

        # Click the chat to open it (with timeout to avoid infinite retries)
        try:
            await chat_element.click(timeout=5000)
        except Exception as click_err:
            log("Skip", f"Could not click chat '{chat_name}': {type(click_err).__name__}")
            return
        await asyncio.sleep(1.5)  # Wait for messages to load

        # === FORUM GROUP DETECTION ===
        # Forum-style groups (with topic channels) have a 'topics-slider' div
        # that intercepts all clicks and causes infinite loops. Detect and escape.
        try:
            # Wait for either the chat input box or the forum topics container to appear
            # This handles slow network loading of the chat column
            try:
                await page.wait_for_selector(
                    ".chat-input-control, .message-input, .Transition_slide .forum-topics, .Transition_slide .topics-container",
                    state="attached",
                    timeout=5000
                )
            except Exception:
                log("Skip", f"Chat panel didn't load properly for {chat_name}")
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
                return
            
            # Check if there is an active message input or a normal message list in the center panel
            has_input = await page.evaluate("() => !!document.querySelector('.chat-input-control, .message-input')")
            has_forum_panel = await page.evaluate("() => !!document.querySelector('.Transition_slide .forum-topics, .Transition_slide .topics-container')")
            
            if not has_input or has_forum_panel:
                log("Skip", f"Forum group detected (has topic channels): {chat_name}")
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
                return
        except Exception:
            pass

        # Get chat title and check if it's a group (now that we're inside)
        chat_title = await get_chat_title(page) or chat_name
        group = await is_group_chat(page)

        # For group chats: only reply in allowed groups, skip all others instantly
        if group:
            if not is_allowed_group(chat_title):
                log("Skip", f"Ignoring non-allowed group: {chat_title}")
                return

        # Read the last incoming message (and potentially fetch its image)
        message_text, msg_id, base64_img = await get_last_incoming_message(page)

        if not message_text or not msg_id:
            log("Skip", "No readable incoming message found")
            return

        # Skip if already replied
        if msg_id in replied_messages:
            log("Skip", f"Already replied to message {msg_id}")
            return

        # For allowed group chats, also check trigger keywords
        if group and not should_reply_in_group(message_text):
            preview = message_text.replace('\\n', ' ')[:50]
            log("Skip", f"Group message doesn't match triggers: {preview}")
            save_replied_message(msg_id)
            return

        preview = message_text.replace('\\n', ' ')[:60]
        log("AI", f'Generating reply for context: "{preview}..."')

        # Human-like delay before replying
        delay = random.uniform(MIN_REPLY_DELAY, MAX_REPLY_DELAY)
        log("Wait", f"Simulating {delay:.1f}s reading time...")
        await asyncio.sleep(delay)

        # Generate reply (pass the image if it exists)
        reply = await generate_reply(message_text, api_key, base64_img)

        if reply == "CREDIT_ERROR":
            # Don't mark as replied — we'll retry once credit is available
            log("Skip", "Skipping due to credit error (will retry later)")
            return

        if not reply:
            log("Skip", "Failed to generate reply, skipping")
            # Mark as replied to avoid retrying the same failed message
            save_replied_message(msg_id)
            return

        # Type and send
        success = await type_and_send(page, reply)
        if success:
            save_replied_message(msg_id)

        # Wait before moving to next chat
        await asyncio.sleep(random.uniform(1, 3))

    except Exception as e:
        log("Error", f"Failed to process chat: {type(e).__name__}: {e}")


# ============================================================================
# SECTION: MAIN LOOP
# ============================================================================


async def switch_to_folder(page: Page, folder_name: str) -> bool:
    """Click a Telegram folder tab (e.g. 'Personal', 'Unread').
    Returns True if the folder was found and clicked, or already active.
    """
    try:
        # Use JS to find the folder tab by its text content
        clicked = await page.evaluate(f"""() => {{
            // Telegram Web K has a .folders-tabs-scrollable container
            const container = document.querySelector('.folders-tabs-scrollable, .folder-tabs, .chatlist-top');
            if (!container) return 'NOT_FOUND';
            
            // Try to find the tab by looking at all clickable elements inside the container
            const tabs = container.querySelectorAll('.chatlist-folder, .folder-tab, div[role="tab"], span[role="tab"], div, span');
            for (const tab of tabs) {{
                // Skip if it doesn't have a click handler or isn't a direct child-ish element
                if (tab.children.length > 3) continue; 
                
                const text = Array.from(tab.childNodes)
                    .filter(node => node.nodeType === Node.TEXT_NODE)
                    .map(node => node.textContent.trim())
                    .join('').toLowerCase();
                    
                if (text === '{folder_name.lower()}') {{
                    // Check if it's already active!
                    let is_active = false;
                    let checkNode = tab;
                    for (let i = 0; i < 3 && checkNode; i++) {{
                        if (checkNode.classList && checkNode.classList.contains('active')) is_active = true;
                        checkNode = checkNode.parentElement;
                    }}
                    
                    if (is_active) return 'ALREADY_ACTIVE';
                    
                    // Found the exact text node! Click its parent block.
                    let clickTarget = tab;
                    while (clickTarget && !clickTarget.classList.contains('chatlist-folder') && !clickTarget.classList.contains('active') && clickTarget !== container) {{
                        if (clickTarget.onclick || getComputedStyle(clickTarget).cursor === 'pointer') break;
                        clickTarget = clickTarget.parentElement;
                    }}
                    (clickTarget || tab).click();
                    return 'CLICKED';
                }}
            }}
            return 'NOT_FOUND';
        }}""")
        if clicked == 'CLICKED':
            log("Folder", f"Switched to '{folder_name}' folder")
            await asyncio.sleep(1)  # Wait for chatlist to refresh
            return True
        elif clicked == 'ALREADY_ACTIVE':
            return True # Successfully kept in the same folder
        else:
            log("Folder", f"Could not find '{folder_name}' folder tab")
            return False
    except Exception as e:
        log("Folder", f"Error switching to '{folder_name}': {e}")
        return False


async def main_loop(page: Page, api_key: str) -> None:
    """Main scanning loop — scans configured folder tabs for unread chats."""
    consecutive_errors = 0
    max_consecutive_errors = 10

    log("Info", f"Scanning folders: {', '.join(SCAN_FOLDERS)}")
    
    current_folder_idx = 0
    loops_in_folder = 0

    while True:
        try:
            # Check if page is still connected
            try:
                await page.title()
            except Exception:
                log("Error", "Telegram tab disconnected. Attempting to reconnect...")
                await asyncio.sleep(10)
                continue

            # Process the current folder instead of switching wildly
            folder = SCAN_FOLDERS[current_folder_idx]
            switched = await switch_to_folder(page, folder)
            
            if switched:
                # Scan for unread chats in this folder
                unread_chats = await get_unread_chats(page)

                if unread_chats:
                    log("Info", f"Found {len(unread_chats)} unread/unreplied chat(s) in '{folder}'")
                    for chat_element, chat_name, subtitle in unread_chats:
                        await process_chat(page, chat_element, chat_name, api_key)
                        # Record state so we don't endlessly loop un-repliable messages
                        save_chat_state(chat_name, subtitle)
                    loops_in_folder = 0 # Had activity, restart clock for staying in this folder

            loops_in_folder += 1
            
            # Switch folder every 6 loops (approx 30s) if we have multiple folders
            if len(SCAN_FOLDERS) > 1 and loops_in_folder >= 6:
                current_folder_idx = (current_folder_idx + 1) % len(SCAN_FOLDERS)
                loops_in_folder = 0

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

    # Init database
    log("Init", "Initializing database state...")
    init_supabase()

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
