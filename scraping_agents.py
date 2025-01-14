import asyncio
from bs4 import BeautifulSoup
import trafilatura
from playwright.async_api import async_playwright
from PIL import Image
import pytesseract
from urllib.parse import urljoin, urlparse
import logging
from io import BytesIO
from typing import List, Dict, Set
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScrapingAgent:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.content_data: List[Dict] = []
        
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to the same domain and is a valid content page."""
        try:
            base_domain = urlparse(self.base_url).netloc
            url_domain = urlparse(url).netloc
            
            # Skip common non-content URLs
            skip_patterns = [
                r'\.(jpg|jpeg|png|gif|css|js|xml|pdf)$',
                r'/wp-admin/',
                r'/wp-includes/',
                r'/feed/',
                r'/tags/',
                r'/page/',
                r'/category/',
                r'/author/',
                r'/cdn-cgi/',
                r'/wp-json/',
            ]
            
            if any(re.search(pattern, url.lower()) for pattern in skip_patterns):
                return False
                
            return base_domain == url_domain
        except:
            return False
            
    async def _extract_page_content(self, page, url: str) -> Dict:
        """Extract structured content from a page."""
        try:
            # Wait for content to load
            await page.wait_for_load_state('networkidle')
            
            # Get the page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.select('script, style, iframe, nav, footer, .header, .footer, .navigation, .menu, .sidebar'):
                element.decompose()
            
            # Extract structured content
            structured_content = {
                'url': url,
                'title': await page.title(),
                'headings': [],
                'main_content': '',
                'metadata': {}
            }
            
            # Extract headings
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                if heading.text.strip():
                    structured_content['headings'].append({
                        'level': heading.name,
                        'text': heading.text.strip()
                    })
            
            # Try to find main content
            main_content = None
            content_selectors = [
                'main',
                'article',
                '[role="main"]',
                '.main-content',
                '#main-content',
                '.content',
                '#content'
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            # Clean and extract text
            if main_content:
                # Remove empty elements and unwanted characters
                for element in main_content.find_all():
                    if len(element.get_text(strip=True)) == 0:
                        element.decompose()
                
                text = main_content.get_text(separator='\n', strip=True)
                text = re.sub(r'\n\s*\n', '\n', text)  # Remove multiple newlines
                structured_content['main_content'] = text
            
            # Extract metadata
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                name = tag.get('name', tag.get('property', ''))
                content = tag.get('content', '')
                if name and content:
                    structured_content['metadata'][name] = content
            
            return structured_content
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    async def _find_links(self, page) -> List[str]:
        """Extract all valid links from the page."""
        try:
            links = set()
            
            # Get all links from the page
            elements = await page.query_selector_all('a[href]')
            for element in elements:
                href = await element.get_attribute('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self._is_valid_url(full_url):
                        links.add(full_url)
            
            return list(links)
            
        except Exception as e:
            logger.error(f"Error finding links: {e}")
            return []

    async def scrape_site(self) -> List[Dict]:
        """Scrape the entire website."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                
                # Create a new page
                page = await context.new_page()
                
                # Configure timeouts
                page.set_default_timeout(30000)
                
                # URLs to process
                urls_to_visit = [self.base_url]
                
                while urls_to_visit and len(self.visited_urls) < 100:  # Limit to 100 pages
                    url = urls_to_visit.pop(0)
                    
                    if url in self.visited_urls:
                        continue
                    
                    try:
                        logger.info(f"Scraping: {url}")
                        
                        # Navigate to the page
                        await page.goto(url, wait_until='networkidle')
                        
                        # Extract content
                        content = await self._extract_page_content(page, url)
                        if content and content['main_content'].strip():
                            self.content_data.append(content)
                        
                        # Find new links
                        new_links = await self._find_links(page)
                        urls_to_visit.extend([link for link in new_links if link not in self.visited_urls])
                        
                        self.visited_urls.add(url)
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error processing {url}: {e}")
                        continue
                
                await browser.close()
                
                # Save the scraped data
                with open('web_scraping_results.json', 'w', encoding='utf-8') as f:
                    json.dump(self.content_data, f, ensure_ascii=False, indent=2)
                
                return self.content_data
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return []

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