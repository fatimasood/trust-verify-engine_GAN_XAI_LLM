#!/usr/bin/env python3
"""
Benchmark TrustVerify against test datasets
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.models.free_ai_detector import FreeAIDetector
from src.evaluation.evaluation_metrics import EvaluationMetrics
from src.utils import logger

def evaluate_on_dataset(csv_path: str, ai_detector):
    """Evaluate detector on labeled dataset"""
    
    logger.info(f"Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    
    if 'text' not in df.columns or 'label' not in df.columns:
        logger.error("Dataset must have 'text' and 'label' columns")
        return None
    
    # Predict
    logger.info(f"Evaluating {len(df)} samples...")
    
    predictions = []
    probabilities = []
    
    for idx, row in df.iterrows():
        result = ai_detector.detect_ai(row['text'])
        predictions.append(1 if result['is_ai_generated'] else 0)
        probabilities.append(result['ai_probability'])
        
        if (idx + 1) % 50 == 0:
            logger.info(f"  Processed {idx+1}/{len(df)}")
    
    # Map labels (assuming: 0=human, 1=ai)
    y_true = df['label'].values
    y_pred = predictions
    y_proba = probabilities
    
    # Calculate metrics
    metrics = EvaluationMetrics.calculate_metrics(y_true, y_pred, y_proba)
    EvaluationMetrics.print_metrics(metrics)
    
    return metrics

def main():
    """Run evaluation"""
    
    logger.info("🧪 TrustVerify Benchmark")
    
    detector = FreeAIDetector(use_ensemble=False)
    
    # Evaluate on test dataset (if available)
    test_file = "data/benchmarks/test_set.csv"
    
    if Path(test_file).exists():
        evaluate_on_dataset(test_file, detector)
    else:
        logger.warning(f"Test file not found: {test_file}")
        logger.info("To run evaluation, create a CSV with 'text' and 'label' columns")

if __name__ == "__main__":
    main()