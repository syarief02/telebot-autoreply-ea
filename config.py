"""
EA Budak Ubat — Bot Configuration
==================================
Edit this file to add new EAs, change knowledge sources,
or update the system prompt. No need to touch auto_reply.py.
"""

# ============================================================================
# BOT SETTINGS
# ============================================================================

CHECK_INTERVAL      = 5        # seconds between scans
MIN_REPLY_DELAY     = 3        # min seconds before replying (human simulation)
MAX_REPLY_DELAY     = 8        # max seconds before replying
TYPING_SPEED        = 0.04     # seconds per character
KNOWLEDGE_CACHE_TTL = 3600     # cache TTL in seconds (1 hour)
MAX_CHARS_PER_SOURCE = 4000   # max chars to extract per URL
MAX_TOKENS_REPLY    = 500      # max tokens for Claude reply

# ============================================================================
# BROWSER SETTINGS
# ============================================================================

BRAVE_PATH        = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
REMOTE_DEBUG_PORT = 9222

# ============================================================================
# CHAT FILTER
# ============================================================================

# Only these groups will receive replies (case-insensitive match).
# All other groups are silently ignored. Private chats always get replies.
# To add more groups, just add to this list:
ALLOWED_GROUP_NAMES = [
    "ea budak ubat",
]

# Keywords that trigger a reply in allowed group chats.
# If a group message doesn't contain any of these, the bot skips it.
GROUP_TRIGGERS = {"ea", "bot", "syarief", "broker", "trading", "?"}

# ============================================================================
# KNOWLEDGE SOURCES — WEBSITE PAGES
# ============================================================================
# Add your product pages here. The bot scrapes text content from each URL.
# To add a new EA: just append its page URL to this list.

WEBSITE_URLS = [
    "https://eabudakubat.com",
    "https://eabudakubat.com/ea-budak-ubat",
    "https://eabudakubat.com/goldmind-ai",
    "https://eabudakubat.com/bracketblitz",
    "https://eabudakubat.com/mathedge-pro",
    "https://eabudakubat.com/aligator-gozaimasu",
    "https://eabudakubat.com/encik-moku",
    "https://eabudakubat.com/guide",
    # --- Add new EA website pages below ---
    # "https://eabudakubat.com/your-new-ea",
]

# ============================================================================
# KNOWLEDGE SOURCES — GITHUB REPOS (REQUIRED)
# ============================================================================
# These are always fetched. If they fail, a warning is logged.

GITHUB_URLS = [
    "https://raw.githubusercontent.com/syarief02/EA_Budak_Ubat/main/README.md",
    "https://raw.githubusercontent.com/syarief02/EA_Budak_Ubat_MT5_Public/main/README.md",
    "https://github.com/syarief02/EA_Budak_Ubat/releases/latest",
    "https://github.com/syarief02/EA_Budak_Ubat_MT5_Public",
    # --- Add new required GitHub repos below ---
]

# ============================================================================
# KNOWLEDGE SOURCES — GITHUB REPOS (OPTIONAL)
# ============================================================================
# These are fetched if available, silently skipped if 404.
# To add a new EA repo: just append its GitHub URL.

GITHUB_OPTIONAL_URLS = [
    "https://github.com/syarief02/BracketBlitz",
    "https://github.com/syarief02/MathEdge-Pro",
    "https://github.com/syarief02/Aligator-Gozaimasu",
    "https://github.com/syarief02/Encik-Moku",
    "https://github.com/syarief02/GoldMind-AI",
    # --- Add new optional GitHub repos below ---
    # "https://github.com/syarief02/Your-New-EA",
]

# ============================================================================
# SYSTEM PROMPT
# ============================================================================
# This is the identity and instructions for the AI. The {knowledge} placeholder
# is automatically replaced with fetched content at runtime.
# Update this if you add new products, change pricing, or update broker links.

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
