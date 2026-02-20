"""
web crawler service


"""

from playwright.async_api import async_playwright
from collections import deque
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, Any

start_urls = [
    "https://primelands.lk/house/en/",
    "https://primelands.lk/land/en/"
]
visited = set()
queue = deque([(url, 0) for url in start_urls])


def extract_content(soup: BeautifulSoup, url: str)-> Dict[str, Any]:
    """ 
    Extract content from soup 
    
    Content : 
        property_id,
        title,
        address,
        price, 
        bedrooms,
        bathrooms,
        sqft,
        amenities,
        agent
    """

    for element in soup.find_all("div", class_="property-card"):
        element.decompose()


    title = soup.title.string if soup.title else url.split("/")[-1]
    print(title) 

    


async def crawl():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)

        while queue:
            url, depth = queue.popleft()

            if depth > 3:
                continue

            try:
                print(f"[{depth}] {url}")
                visited.add(url)
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                try:
                    await page.wait_for_selector("body", timeout=10000)
                    await page.wait_for_timeout(3000)

                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)
                except:
                    await page.wait_for_timeout(5000)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                extract_content(soup, url)   


                if depth < 3:
                    links_added = 0
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if href.startswith("http") and href not in visited:
                            queue.append((href, depth + 1))
                            visited.add(href)
                            links_added += 1
                    if links_added > 0:
                        print(f"Added {links_added} new links")
                
            except Exception as e:
                print("error", e)

asyncio.run(crawl())