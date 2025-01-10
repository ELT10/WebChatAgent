import asyncio
from bs4 import BeautifulSoup
import trafilatura
from playwright.async_api import async_playwright
from PIL import Image
import pytesseract
from urllib.parse import urljoin, urlparse
import logging
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScrapingAgent:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited_urls = set()
        
    def _is_valid_url(self, url):
        """Check if URL belongs to the same domain."""
        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain == url_domain
    
    def _extract_internal_links(self, soup, current_url):
        """Extract internal links from the page."""
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)
            if self._is_valid_url(full_url):
                links.add(full_url)
        return links

    async def scrape_site(self):
        urls_to_visit = [self.base_url]
        collected_data = []
        
        while urls_to_visit:
            url = urls_to_visit.pop(0)
            if url in self.visited_urls:
                continue
                
            try:
                logger.info(f"Scraping: {url}")
                downloaded = trafilatura.fetch_url(url)
                
                if downloaded:
                    # Extract clean text
                    text = trafilatura.extract(downloaded)
                    
                    if text:
                        collected_data.append({
                            "url": url,
                            "content": text
                        })
                    
                    # Find new links
                    soup = BeautifulSoup(downloaded, 'html.parser')
                    new_urls = self._extract_internal_links(soup, url)
                    urls_to_visit.extend([u for u in new_urls if u not in self.visited_urls])
                
                self.visited_urls.add(url)
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                
        return collected_data

class VisualScrapingAgent:
    def __init__(self, base_url):
        self.playwright = None
        self.browser = None
        self.base_url = base_url
        self.visited_urls = set()
    
    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        
    async def cleanup(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
    def _is_valid_url(self, url):
        """Check if URL belongs to the same domain."""
        base_domain = urlparse(self.base_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain == url_domain

    async def _extract_internal_links(self, page):
        """Extract internal links from the page using Playwright."""
        links = set()
        elements = await page.query_selector_all('a[href]')
        for element in elements:
            href = await element.get_attribute('href')
            if href:
                full_url = urljoin(self.base_url, href)
                if self._is_valid_url(full_url):
                    links.add(full_url)
        return links

    async def scrape_site(self):
        if not self.browser:
            await self.setup()

        urls_to_visit = [self.base_url]
        collected_data = []

        try:
            while urls_to_visit:
                url = urls_to_visit.pop(0)
                if url in self.visited_urls:
                    continue

                try:
                    logger.info(f"Visually scraping: {url}")
                    page = await self.browser.new_page()
                    await page.goto(url)
                    await page.wait_for_load_state('networkidle')

                    # Capture and process screenshot
                    screenshot_bytes = await page.screenshot(full_page=True)
                    image = Image.open(BytesIO(screenshot_bytes))
                    text = pytesseract.image_to_string(image)

                    if text:
                        collected_data.append({
                            "url": url,
                            "content": text
                        })

                    # Find new links
                    new_urls = await self._extract_internal_links(page)
                    urls_to_visit.extend([u for u in new_urls if u not in self.visited_urls])

                    self.visited_urls.add(url)
                    await page.close()

                    # Rate limiting
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"Error visually scraping {url}: {e}")

            return collected_data

        finally:
            await self.cleanup() 