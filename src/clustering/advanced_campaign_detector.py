"""
Detect coordinated fake review campaigns using HDBSCAN + stylometric clustering
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.cluster import HDBSCAN
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
from src.utils import logger

class AdvancedCampaignDetector:
    """
    Detect fake review rings using:
    - Semantic embeddings (review similarity)
    - Stylometric features (writing style)
    - Metadata clustering (timing, products, authors)
    """
    
    def __init__(self, min_cluster_size: int = 3):
        """Initialize campaign detector"""
        
        self.min_cluster_size = min_cluster_size
        
        logger.info("Loading sentence embeddings model...")
        self.embeddings_model = SentenceTransformer('all-mpnet-base-v2')
        self.embeddings_model.eval()
        
        logger.info("✓ Campaign detector ready")
    
    def extract_stylometric_features(self, text: str) -> Dict:
        """Extract writing style features"""
        
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()
        
        if not words or not sentences:
            return {}
        
        return {
            'avg_word_length': np.mean([len(w) for w in words]),
            'avg_sentence_length': np.mean([len(s.split()) for s in sentences]),
            'word_variety': len(set(words)) / len(words),
            'punctuation_density': (text.count('!') + text.count('?')) / len(words),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text),
            'exclamation_freq': text.count('!') / len(sentences) if sentences else 0,
            'quote_freq': text.count('"') / len(sentences) if sentences else 0,
        }
    
    def detect_campaigns(self, reviews: List[Dict]) -> Tuple[pd.DataFrame, Dict]:
        """
        Detect coordinated fake review campaigns
        
        Args:
            reviews: List of dicts with keys: text, author, timestamp, product_id
        
        Returns:
            (reviews_with_clusters, campaign_report)
        """
        
        if len(reviews) < self.min_cluster_size:
            logger.warning(f"Not enough reviews ({len(reviews)}) for clustering")
            return pd.DataFrame(reviews), {'campaigns': []}
        
        logger.info(f"Analyzing {len(reviews)} reviews for coordinated campaigns...")
        
        texts = [r['text'] for r in reviews]
        
        # Get embeddings
        logger.info("Computing text embeddings...")
        embeddings = self.embeddings_model.encode(texts, show_progress_bar=True)
        
        # Extract stylometric features
        logger.info("Extracting stylometric features...")
        stylometric = np.array([
            list(self.extract_stylometric_features(text).values())
            for text in texts
        ])
        
        # Normalize features
        scaler = StandardScaler()
        stylometric_scaled = scaler.fit_transform(stylometric)
        
        # Combine embeddings + stylometric (70-30 weighted)
        combined = np.hstack([
            embeddings * 0.7,
            stylometric_scaled * 0.3
        ])
        
        # HDBSCAN clustering
        logger.info("Clustering reviews with HDBSCAN...")
        clusterer = HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=2,
            cluster_selection_epsilon=0.5
        )
        
        labels = clusterer.fit_predict(combined)
        
        # Create results DataFrame
        df = pd.DataFrame(reviews)
        df['cluster_id'] = labels
        df['is_noise'] = labels == -1
        
        # Generate report
        report = self._generate_report(df, reviews)
        
        return df, report
    
    def _generate_report(self, df: pd.DataFrame, reviews: List[Dict]) -> Dict:
        """Generate human-readable campaign report"""
        
        report = {
            'total_reviews': len(df),
            'clustered_reviews': int((df['cluster_id'] != -1).sum()),
            'noise_reviews': int((df['cluster_id'] == -1).sum()),
            'num_clusters': len(set(df['cluster_id'])) - (1 if -1 in df['cluster_id'].values else 0),
            'campaigns': []
        }
        
        # Analyze each cluster
        for cluster_id in df[df['cluster_id'] != -1]['cluster_id'].unique():
            cluster = df[df['cluster_id'] == cluster_id]
            
            red_flags = []
            
            # Flag 1: All reviews for same product
            unique_products = cluster['product_id'].nunique()
            if unique_products == 1:
                red_flags.append("All reviews target same product")
            
            # Flag 2: Very similar ratings
            if 'rating' in cluster.columns:
                ratings = cluster['rating'].values
                if np.std(ratings) < 0.5:
                    red_flags.append(f"All reviews have identical ratings ({ratings[0]})")
            
            # Flag 3: Temporal clustering (posted close together)
            if 'timestamp' in cluster.columns:
                timestamps = pd.to_datetime(cluster['timestamp'])
                time_span_days = (timestamps.max() - timestamps.min()).days
                if 0 < time_span_days < 7 and len(cluster) > 2:
                    red_flags.append(f"All posted within {time_span_days} days")
            
            # Flag 4: Multiple accounts posting identical text
            text_duplicates = cluster['text'].value_counts()
            if (text_duplicates > 1).sum() > 0:
                red_flags.append(f"{(text_duplicates > 1).sum()} identical reviews detected")
            
            campaign_info = {
                'cluster_id': int(cluster_id),
                'size': len(cluster),
                'unique_authors': cluster['author'].nunique(),
                'unique_products': unique_products,
                'suspicion_level': 'HIGH' if len(red_flags) >= 3 else 'MEDIUM' if len(red_flags) >= 1 else 'LOW',
                'red_flags': red_flags,
                'sample_reviews': cluster[['author', 'text', 'timestamp']].head(2).to_dict('records')
            }
            
            report['campaigns'].append(campaign_info)
        
        # Sort by suspicion level
        report['campaigns'].sort(key=lambda x: ['LOW', 'MEDIUM', 'HIGH'].index(x['suspicion_level']))
        
        return report