#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.scraper.universal_scraper import UniversalScraper
from src.data_collection.database_manager import DatabaseManager
from src.utils import logger

def main():
    db = DatabaseManager()
    scraper = UniversalScraper()
    # Example: scrape a Daraz product page
    url = input("Enter product URL to scrape: ")
    data = scraper.scrape(url)
    if data.get('text'):
        review = {
            'review_id': 'manual_1',
            'text': data['text'],
            'rating': None,
            'author_name': 'scraped',
            'author_id': 'scraped',
            'timestamp': 'now',
            'product_id': url.split('/')[-1],
            'source': url,
            'verified_purchase': False
        }
        db.insert_reviews([review])
        logger.info("Scraped and saved")
    else:
        logger.error("No text extracted")

if __name__ == "__main__":
    main()