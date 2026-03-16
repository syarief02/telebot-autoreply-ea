import asyncio
from playwright.async_api import async_playwright

async def debug_tabs():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        tabs = await page.evaluate("""() => {
            const elements = document.querySelectorAll(".tabs-tab, .menu-horizontal-div > li, .folder-tabs > span, [class*='tabs'], [class*='folder']");
            return Array.from(elements).map(e => ({
                tag: e.tagName,
                className: e.className,
                text: e.textContent.trim(),
                innerText: e.innerText,
                html: e.innerHTML.substring(0, 50)
            })).filter(t => t.text.includes("Personal") || t.text.includes("Unread") || t.text.includes("All"));
        }""")
        print("FOUND TABS:")
        for t in tabs:
            print(t)

asyncio.run(debug_tabs())
