"""
web crawler service


"""

from playwright.async_api import async_playwright
from collections import deque
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Set
import re
from urllib.parse import urljoin ,urlparse
from markdownify import markdownify as md   
import json 
# from src.real_state.config import CRAWL_OUT_DIR


class PrimeLandWebCrawler:
    def __init__(self, base_url: str, max_depth: int, exclude_patterns: List[str]):
        self.base_url = base_url
        self.max_depth = max_depth
        self.exclude_patterns = exclude_patterns
        self.visited : Set[str] = set()
        self.documents : List[Dict[str, Any]] = []
        print("Starting crawl")

    def should_crawl(self, url: str) -> bool:
        """ check if url should be crawled base on rulz """

        if url in self.visited:
            return False

        if not url.startswith(self.base_url):
            return False
        
        for pattern in self.exclude_patterns:
            if pattern in url:
                return False
        
        if re.search(r'\.(jpg|jpeg|png|gif|pdf|zip|exe)$', url, re.I):
            return False
        
        return True


    def extract_content(self, soup: BeautifulSoup, url: str, start_urls: List[str])-> Dict[str, Any]:
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

        for element in soup(["script", "style", "noscript", "iframe"]):
            element.decompose()


        if url not in start_urls:
            

        # Create a new blank container to hold ONLY the advertisement pieces
            ad_container = soup.new_tag('div')

            # 1. collect project id 
            project_id = soup.find("input", id="iProjectID")["value"]
            ad_container.append(f"Project ID: {project_id}")
            
            # 2. Grab Title & Location
            title_elem = soup.find('h1', class_='project_name')
            if title_elem:
                ad_container.append(title_elem)
                # Location is usually in the <p> tag right after the title
                loc_parent = title_elem.parent
                if loc_parent:
                    loc_elem = loc_parent.find('p')
                    if loc_elem:
                        ad_container.append(loc_elem)

            # 3. Grab Price & Unit
            price_elem = soup.find('h1', class_='text_red')
            if price_elem:
                ad_container.append(price_elem)
                # The "PER PERCH UPWARDS" text
                unit_elem = price_elem.find_next_sibling('p', class_='fst-italic')
                if unit_elem:
                    ad_container.append(unit_elem)

            # 4. Grab the main details column (About, Payment Plan, Facilities)
            # In the provided HTML, this is inside a specific Bootstrap column class
            details_col = soup.find('div', class_=re.compile(r'col-xxl-8.*col-lg-8'))
            if details_col:
                # We want to remove the interactive Map/Location tabs at the bottom of the ad
                tabs_ul = details_col.find('ul', class_='arrow_tab')
                if tabs_ul:
                    tabs_ul.decompose()
                tabs_content = details_col.find('div', id='pills-tabContent')
                if tabs_content:
                    tabs_content.decompose()
                        
                ad_container.append(details_col)

            # Convert our custom container to Markdown
            if ad_container.contents:
                content_md = md(str(ad_container), heading_style="ATX")
            else:
                content_md = ""

            # Clean up the markdown
            content_md = re.sub(r'\n{3,}', '\n\n', content_md)
            content_md = content_md.strip()

            # Extract headings for metadata
            headings = [h.get_text(strip=True) for h in ad_container.find_all(['h1', 'h2', 'h3', 'h4'])]
            
            # Fallback title if ad title isn't found
            page_title = title_elem.get_text(strip=True) if title_elem else (soup.title.string if soup.title else "Untitled")

        # Extract internal links
        links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if not href:
                continue
            if href.startswith('/'):
                href = self.base_url + href
            elif not href.startswith('http'):
                href = urljoin(url, href)
            
            if href.startswith(self.base_url):
                href = href.split('#')[0].split('?')[0]
                if href and href != url:
                    links.append(href)

        data =  {
            "title": page_title.strip() if url not in start_urls else "",
            "project_id": project_id if url not in start_urls else "",
            "headings": headings if url not in start_urls else [],
            "content": content_md if url not in start_urls else "",
            "links": list(set(links)),
            }
        return data



    async def crawl_async(self, start_urls: List[str], request_delay: float = 2.0,) -> List[Dict[str, Any]]:
        queue = deque([(url, 0) for url in start_urls])


        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.set_default_timeout(30000)

            while queue:
                url, depth = queue.popleft()
                if depth > self.max_depth or not self.should_crawl(url):
                    continue

                try:
                    print(f"🔍 [{depth}] {url}")
                    self.visited.add(url)

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
                    
                    doc_data = self.extract_content(soup, url, start_urls)
                    doc_data['url'] = url
                    doc_data['depth_level'] = depth
                    if url not in start_urls:
                        if len(doc_data['content']) >= 100:
                            self.documents.append(doc_data)
                            print(f"   ✅ Saved ({len(doc_data['content'])} chars, {len(doc_data['links'])} links found)")
                        else:
                            print(f"   ⚠️ Skipped ({len(doc_data['content'])} chars) - too short")

                    
                        if depth < self.max_depth:
                            links_added = 0
                            for link in doc_data['links']:
                                if link not in self.visited and link not in [item[0] for item in queue]:
                                    queue.append((link, depth-1))
                                    links_added += 1
                            if links_added > 0:
                                print(f" 📎 Added {links_added} new URLs to queue (depth {depth + 1})")

                        print(f" 📊 Progress: {len(self.documents)} docs saved, {len(self.visited)} visited, {len(queue)} in queue")
                    else:
                        if depth < self.max_depth:
                            links_added = 0
                            for link in doc_data['links']:
                                if link not in self.visited and link not in [item[0] for item in queue]:
                                    queue.append((link, depth-1))
                                    links_added += 1
                            if links_added > 0:
                                print(f" 📎 Added {links_added} new URLs to queue (depth {depth + 1})")
                        print(f"   ⚠️ Skipped ({url}) - not a property page")
                    await asyncio.sleep(request_delay)
                
                except Exception as e:
                    error_msg = str(e)
                    if "404" in error_msg or "net::ERR_" in error_msg:
                        print(f"   ⚠️ Skipped ({url}) - 404 or network error")
                    else:
                        print(f"   ❌ Error: {error_msg[:100]}")
                    continue

            await browser.close()
        
        return self.documents





    def crawl(self, start_urls: List[str], request_delay: float = 2.0) -> List[Dict[str, Any]]:
        print("Starting crawl")
        return asyncio.run(self.crawl_async(start_urls, request_delay))


__all__ = ["PrimeLandWebCrawler"]




if __name__ == "__main__":
    base_url = "https://www.primelands.lk"
    start_urls = [
        "https://www.primelands.lk/house/en",
        "https://www.primelands.lk/land/en",
        "https://www.primelands.lk/apartment/ongoing/en",
        "https://www.primelands.lk/apartment/en",
        "https://www.primelands.lk/"
        "https://www.primelands.lk/en",
        "https://www.primelands.lk/close-to-railway-stations/en",
        "https://www.primelands.lk/close-to-Airport/en",
        "https://www.primelands.lk/close-to-highways/en",
        "https://www.primelands.lk/mountain-view/en",
        "https://www.primelands.lk/coconut-land/en",
        "https://www.primelands.lk/down-south-lands/en",
        "https://www.primelands.lk/close-to-ancient-city-lands/en",
        "https://www.primelands.lk/waterfront-land/en",
        "https://www.primelands.lk/up-country-lands/en",
        "https://www.primelands.lk/paddy-field-facing-lands/en"
    ]

    exclude_patterns = [
        "/login",
        "/register",
        "/contact",
        "/about",
        "/privacy-policy",
        "/terms-of-service",
        "/sitemap",
        "/si",
        "/terms-and-conditions",
        "/careers",
        "/news",
        "/portfolio-property",
        "/city",
        "/blog",
        "/disclaimer",
        "/online-publications",
        "/kyc",
        "/tam",
        "/upcoming-projects",
        "/sell-your-land",
        "/services", 
        "/virtual-tour",
        "/testimonial",
        "/district",
    ]

    max_depth=2
    request_delay=2.0
    json_path = "data/primelands_corpus.jsonl"


    crawler = PrimeLandWebCrawler(base_url, max_depth=max_depth, exclude_patterns=exclude_patterns)
    documents = crawler.crawl(start_urls, request_delay=request_delay)

    for i, doc in enumerate(documents):
        url_path = urlparse(doc['url']).path.strip('/').replace('/', '_')
        if not url_path:
            url_path = "homepage"
        filename = f"{i:03d}_{url_path}.md"
        
        md_file = "data/primeland_markdown/" + filename
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {doc['title']}\n\n")
            f.write(f"**URL**: {doc['url']}\n\n")
            f.write(f"**Depth**: {doc['depth_level']}\n\n")
            f.write("---\n\n")
            f.write(doc['content'])

    print(f"✅ Saved {len(documents)} markdown files to {md_file}")
    
    with open(json_path, 'w', encoding='utf-8') as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            
    print(f"\n✅ Crawl completed. Saved {(documents)} documents.")
