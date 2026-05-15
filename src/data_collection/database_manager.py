import sqlite3
import pandas as pd
from src.utils import logger

class DatabaseManager:
    def __init__(self, db_path="data/reviews.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            text TEXT,
            rating REAL,
            author_name TEXT,
            author_id TEXT,
            timestamp TEXT,
            product_id TEXT,
            source TEXT,
            verified_purchase INTEGER
        )''')
        self.conn.commit()

    def insert_reviews(self, reviews):
        inserted = 0
        for r in reviews:
            try:
                self.conn.execute('''INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?,?,?,?,?)''',
                    (r.get('review_id'), r.get('text'), r.get('rating'), r.get('author_name'),
                     r.get('author_id'), r.get('timestamp'), r.get('product_id'),
                     r.get('source'), 1 if r.get('verified_purchase') else 0))
                inserted += 1
            except Exception as e:
                logger.error(f"Insert error: {e}")
        self.conn.commit()
        return {'inserted': inserted}

    def get_reviews(self, limit=100):
        return pd.read_sql(f"SELECT * FROM reviews LIMIT {limit}", self.conn)

    def get_stats(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT source) FROM reviews")
        sources = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT product_id) FROM reviews")
        products = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT author_id) FROM reviews")
        authors = cur.fetchone()[0]
        cur.execute("SELECT AVG(rating) FROM reviews WHERE rating IS NOT NULL")
        avg_rating = cur.fetchone()[0] or 0
        return {'total_reviews': total, 'unique_sources': sources, 'unique_products': products,
                'unique_authors': authors, 'average_rating': avg_rating}