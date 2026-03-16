import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = b.contexts[0].pages[0]
        html = await page.evaluate('''() => {
            const tabs = document.querySelectorAll('.chatlist-top, .tabs-tab, .folder-tabs, .folders-tabs-scrollable');
            let out = "";
            for (let t of tabs) {
                out += "CLASS: " + t.className + "\\n";
                out += "INNERTEXT: " + t.innerText + "\\n";
                out += "---\\n";
            }
            return out;
        }''')
        
        with open("tabs_dump.txt", "w", encoding="utf-8") as f:
            f.write(html)
        print("Done writing to tabs_dump.txt")

asyncio.run(debug())
