import torch
import os
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from src.utils import logger
from dotenv import load_dotenv

load_dotenv()

class FreeAIDetector:
    def __init__(self, model_name="microsoft/deberta-v3-base", use_ensemble=False, use_hybrid=False):
        # Check for Groq API key
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if self.groq_api_key and self.groq_api_key.strip() and not self.groq_api_key.startswith('gsk_'):
            logger.warning("GROQ_API_KEY seems invalid (should start with 'gsk_')")
            self.groq_api_key = None

        if self.groq_api_key:
            logger.info("🌟 Groq API key found using Llama 3 for AI detection")
            self._init_groq()
        else:
            logger.info("💻 No valid GROQ_API_KEY using local DeBERTa model")
            self._init_local(model_name, use_ensemble, use_hybrid)

    def _init_groq(self):
        try:
            from groq import Groq
            self.client = Groq(api_key=self.groq_api_key)
            self.mode = 'groq'
            logger.info("✓ Groq client ready")
        except ImportError:
            logger.warning("Groq package not installed. Run: pip install groq")
            self._init_local()

    def _init_local(self, model_name="microsoft/deberta-v3-base", use_ensemble=False, use_hybrid=False):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = model_name
        self.mode = 'local'
        logger.info(f"Loading local {model_name} on {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def detect_ai(self, text: str) -> dict:
        if hasattr(self, 'mode') and self.mode == 'groq':
            return self._detect_with_groq(text)
        else:
            return self._detect_with_local(text)

    def _detect_with_groq(self, text: str) -> dict:
        try:
            prompt = f"""Analyze if the following text is AI-generated (ChatGPT, GPT-4, etc.) or human-written.
Text: "{text[:1000]}"
Answer with only a number between 0 and 1, where 0 = definitely human, 1 = definitely AI.
Number:"""
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=10
            )
            result = response.choices[0].message.content.strip()
            match = re.search(r'(\d+\.?\d*)', result)
            ai_prob = float(match.group(1)) if match else 0.5
            ai_prob = max(0.0, min(1.0, ai_prob))
            return {
                'ai_probability': ai_prob,
                'is_ai_generated': ai_prob > 0.5,
                'confidence': abs(ai_prob - 0.5) * 2,
                'mode': 'groq-llama3'
            }
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return self._detect_with_local(text)

    def _detect_with_local(self, text: str) -> dict:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        ai_prob = float(probs[1]) if len(probs) > 1 else 0.5
        return {
            'ai_probability': ai_prob,
            'is_ai_generated': ai_prob > 0.5,
            'confidence': abs(ai_prob - 0.5) * 2,
            'mode': self.model_name
        }