import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from src.utils import logger
import numpy as np

class FreeAIDetector:
    def __init__(self, model_name="microsoft/deberta-v3-base", use_ensemble=False, use_hybrid=False):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = model_name
        self.use_ensemble = use_ensemble
        logger.info(f"Loading AI detector {model_name} on {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def detect_ai(self, text: str) -> dict:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        ai_prob = float(probs[1]) if len(probs) > 1 else 0.5
        return {
            'ai_probability': ai_prob,
            'is_ai_generated': ai_prob > 0.5,
            'confidence': abs(ai_prob - 0.5) * 2,
            'mode': 'local_deberta'
        }