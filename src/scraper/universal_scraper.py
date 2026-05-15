import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.utils import logger
import re
import time

class UniversalScraper:
    def scrape(self, url: str) -> dict:
        if "daraz" in url.lower():
            return self._scrape_daraz(url)
        elif "amazon" in url.lower():
            return self._scrape_amazon(url)
        elif "reddit" in url.lower():
            return self._scrape_reddit(url)
        else:
            return self._scrape_generic(url)

    def _scrape_daraz(self, url: str) -> dict:
        """Improved Daraz scraper with better timeout and headers"""
        try:
            logger.info(f"Scraping Daraz: {url}")
            
            with sync_playwright() as p:
                # Launch with more realistic settings
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                page = browser.new_page()
                
                # Set realistic user agent and headers
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                })
                
                # Increase timeout and wait for network to be idle
                page.goto(url, timeout=60000, wait_until='domcontentloaded')
                
                # Wait a bit for dynamic content
                time.sleep(3)
                
                # Try to wait for product title
                try:
                    page.wait_for_selector('span.pdp-mod-product-badge-title, h1.pdp-product-title', timeout=10000)
                except:
                    logger.warning("Product title selector not found, continuing anyway")
                
                content = page.content()
                browser.close()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try multiple selectors for title
            title = (
                soup.select_one('span.pdp-mod-product-badge-title') or
                soup.select_one('h1.pdp-product-title') or
                soup.select_one('div.product-title') or
                soup.select_one('meta[property="og:title"]')
            )
            
            # Try multiple selectors for price
            price = (
                soup.select_one('div.pdp-product-price') or
                soup.select_one('span.price') or
                soup.select_one('div.price')
            )
            
            # Extract product description
            description = (
                soup.select_one('div.pdp-product-description') or
                soup.select_one('div.product-description')
            )
            
            # Extract reviews if available
            reviews = soup.select('div.review-content, div.item-content')
            review_texts = [r.get_text(strip=True) for r in reviews[:5] if r.get_text(strip=True)]
            
            # Get title text
            title_text = ""
            if title:
                if title.name == 'meta':
                    title_text = title.get('content', '')
                else:
                    title_text = title.get_text(strip=True)
            
            result = {
                'title': title_text or 'No title found',
                'price': price.get_text(strip=True) if price else 'Price not available',
                'description': description.get_text(strip=True)[:500] if description else '',
                'text': ' '.join(review_texts) if review_texts else description.get_text(strip=True)[:1000] if description else title_text,
                'reviews_count': len(review_texts)
            }
            
            logger.info(f"✓ Daraz scrape successful: {result['title'][:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Daraz scrape failed: {e}")
            return self._scrape_generic(url)  # Fallback to generic scraper

    def _scrape_amazon(self, url: str) -> dict:
        """Amazon scraper with improved headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
        }
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.select_one('#productTitle')
            # Try to get reviews
            reviews = soup.select('div.review-text')
            review_texts = [r.get_text(strip=True) for r in reviews[:3]]
            return {
                'title': title.get_text(strip=True) if title else 'No title',
                'text': ' '.join(review_texts) if review_texts else title.get_text(strip=True) if title else '',
                'reviews_count': len(review_texts)
            }
        except Exception as e:
            logger.error(f"Amazon scrape failed: {e}")
            return {'text': ''}

    def _scrape_reddit(self, url: str) -> dict:
        """Reddit scraper"""
        try:
            api_url = url.replace('reddit.com', 'reddit.com') + '.json'
            headers = {'User-Agent': 'TrustVerify/1.0 (Educational Research)'}
            resp = requests.get(api_url, headers=headers, timeout=15)
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                post = data[0]['data']['children'][0]['data']
                return {
                    'title': post.get('title', ''),
                    'text': post.get('selftext', '')[:2000],
                    'author': post.get('author', '')
                }
            return {'text': ''}
        except Exception as e:
            logger.error(f"Reddit scrape failed: {e}")
            return {'text': ''}

    def _scrape_generic(self, url: str) -> dict:
        """Generic fallback scraper"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        try:
            resp = requests.get(url, timeout=15, headers=headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            text = ' '.join(soup.stripped_strings)
            return {'text': text[:2000]}
        except Exception as e:
            logger.error(f"Generic scrape failed: {e}")
            return {'text': '', 'error': str(e)}