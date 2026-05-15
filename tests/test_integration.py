"""
Integration tests for all TrustVerify components
"""

import pytest
import pandas as pd
from datetime import datetime

# Sample data
SAMPLE_REVIEWS = [
    {
        'review_id': '1',
        'text': 'This product is amazing! It works perfectly and exceeded my expectations. Highly recommended!',
        'rating': 5,
        'author': 'user_123',
        'author_id': 'u123',
        'timestamp': '2024-01-15',
        'product_id': 'p001',
        'verified_purchase': True
    },
    {
        'review_id': '2',
        'text': 'Furthermore, the comprehensive functionality of this remarkable product facilitates enhanced user engagement and operational efficiency.',
        'rating': 5,
        'author': 'reviewer_456',
        'author_id': 'u456',
        'timestamp': '2024-01-16',
        'product_id': 'p001',
        'verified_purchase': False
    }
]

def test_ai_detector():
    """Test AI text detection"""
    from src.models import FreeAIDetector
    
    detector = FreeAIDetector()
    
    # Test human text
    human_result = detector.detect_ai(SAMPLE_REVIEWS[0]['text'])
    print(f"\nHuman text: {human_result['ai_probability']:.2%}")
    assert human_result['ai_probability'] < 0.7, "Human text misclassified"
    
    # Test AI text
    ai_result = detector.detect_ai(SAMPLE_REVIEWS[1]['text'])
    print(f"AI text: {ai_result['ai_probability']:.2%}")
    assert ai_result['ai_probability'] > 0.3, "AI text not detected"

def test_campaign_clustering():
    """Test campaign detection"""
    from src.clustering.advanced_campaign_detector import AdvancedCampaignDetector
    
    detector = AdvancedCampaignDetector()
    results_df, report = detector.detect_campaigns(SAMPLE_REVIEWS)
    
    print(f"\nCampaign Report: {report}")
    assert len(results_df) == len(SAMPLE_REVIEWS)

def test_database():
    """Test database persistence"""
    from src.data_collection.database_manager import DatabaseManager
    
    db = DatabaseManager(db_path=":memory:")  # In-memory for testing
    
    # Insert reviews
    stats = db.insert_reviews(SAMPLE_REVIEWS)
    assert stats['inserted'] == len(SAMPLE_REVIEWS)
    
    # Retrieve
    df = db.get_reviews()
    assert len(df) == len(SAMPLE_REVIEWS)

def test_end_to_end():
    """Test full pipeline"""
    from src.models import FreeAIDetector
    from src.clustering.advanced_campaign_detector import AdvancedCampaignDetector
    
    print("\n=== END-TO-END TEST ===")
    
    # 1. Detect AI
    detector = FreeAIDetector()
    ai_results = [detector.detect_ai(r['text']) for r in SAMPLE_REVIEWS]
    print(f"✓ AI detection complete: {len(ai_results)} results")
    
    # 2. Detect campaigns
    campaign_detector = AdvancedCampaignDetector()
    df, report = campaign_detector.detect_campaigns(SAMPLE_REVIEWS)
    print(f"✓ Campaign detection complete: {report['num_clusters']} clusters")
    
    print("\n✅ Full pipeline working!")

if __name__ == "__main__":
    print("Running integration tests...")
    
    try:
        test_ai_detector()
        print("✓ AI detector test passed")
    except Exception as e:
        print(f"✗ AI detector test failed: {e}")
    
    try:
        test_campaign_clustering()
        print("✓ Campaign clustering test passed")
    except Exception as e:
        print(f"✗ Campaign test failed: {e}")
    
    try:
        test_database()
        print("✓ Database test passed")
    except Exception as e:
        print(f"✗ Database test failed: {e}")
    
    try:
        test_end_to_end()
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")