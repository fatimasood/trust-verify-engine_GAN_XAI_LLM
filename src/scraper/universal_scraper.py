import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.utils import logger
import re

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
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=10000)
                content = page.content()
                browser.close()
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.select_one('span.pdp-mod-product-badge-title')
            price = soup.select_one('div.pdp-product-price')
            return {'title': title.get_text(strip=True) if title else '', 'price': price.get_text(strip=True) if price else '', 'text': title.get_text(strip=True) if title else ''}
        except Exception as e:
            logger.error(f"Daraz scrape failed: {e}")
            return {'error': str(e), 'text': ''}

    def _scrape_amazon(self, url: str) -> dict:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.select_one('#productTitle')
        return {'title': title.get_text(strip=True) if title else '', 'text': title.get_text(strip=True) if title else ''}

    def _scrape_reddit(self, url: str) -> dict:
        api_url = url.replace('reddit.com', 'reddit.com/r') + '.json'
        headers = {'User-Agent': 'TrustVerify/1.0'}
        resp = requests.get(api_url, headers=headers, timeout=10)
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            post = data[0]['data']['children'][0]['data']
            return {'title': post.get('title', ''), 'text': post.get('selftext', '')}
        return {'text': ''}

    def _scrape_generic(self, url: str) -> dict:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = ' '.join(soup.stripped_strings)
        return {'text': text[:2000]}