"""
Comprehensive evaluation metrics for TrustVerify
"""

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import pandas as pd
from typing import Dict, List

class EvaluationMetrics:
    """Calculate and report evaluation metrics"""
    
    @staticmethod
    def calculate_metrics(y_true: List[int], y_pred: List[int], y_proba: List[float] = None) -> Dict:
        """
        Calculate comprehensive metrics
        
        Args:
            y_true: Ground truth labels (0=human, 1=AI)
            y_pred: Predicted labels
            y_proba: Predicted probabilities
        
        Returns:
            Dictionary with all metrics
        """
        
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred),
            'recall': recall_score(y_true, y_pred),
            'f1': f1_score(y_true, y_pred),
        }
        
        if y_proba:
            metrics['auc_roc'] = roc_auc_score(y_true, y_proba)
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        metrics['specificity'] = tn / (tn + fp)
        metrics['sensitivity'] = tp / (tp + fn)
        
        return metrics
    
    @staticmethod
    def print_metrics(metrics: Dict):
        """Pretty print metrics"""
        print("\n=== EVALUATION METRICS ===")
        print(f"Accuracy:   {metrics['accuracy']:.4f}")
        print(f"Precision:  {metrics['precision']:.4f}")
        print(f"Recall:     {metrics['recall']:.4f}")
        print(f"F1-Score:   {metrics['f1']:.4f}")
        if 'auc_roc' in metrics:
            print(f"AUC-ROC:    {metrics['auc_roc']:.4f}")