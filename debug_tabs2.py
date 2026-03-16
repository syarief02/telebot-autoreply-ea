import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = b.contexts[0].pages[0]
        html = await page.evaluate('''() => {
            const tabs = document.querySelectorAll('.chatlist-top, .tabs-tab, .folder-tabs');
            return Array.from(tabs).map(t => {
                return {
                    className: t.className,
                    html: t.outerHTML.substring(0, 500)
                };
            });
        }''')
        for h in html:
            print("CLASS:", h['className'])
            print("HTML:", h['html'])
            print("---")

asyncio.run(debug())
