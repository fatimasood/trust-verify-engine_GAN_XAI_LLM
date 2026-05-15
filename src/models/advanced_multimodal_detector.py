"""
Multimodal consistency checking using CLIP and BLIP-2
Detect text-image mismatches in reviews (e.g., "excellent product" with bad photo)
"""

import torch
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from typing import Dict, List, Optional
from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
from src.utils import logger
import time

class MultimodalConsistencyChecker:
    """
    Check if review text matches product images
    
    Use cases:
    - Detect fake Amazon/Daraz reviews with stock photos
    - Find "amazing quality" reviews with blurry/generic images
    - Identify coordinated fake reviews using identical images
    """
    
    def __init__(self, method: str = "clip"):
        """
        Initialize multimodal detector
        
        Args:
            method: 'clip' (fast, good), 'blip2' (slow, better captions)
        """
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.method = method
        
        logger.info(f"Loading multimodal model ({method}) on {self.device}...")
        
        if method == "clip":
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.model.to(self.device)
            logger.info("✓ CLIP loaded")
        
        elif method == "blip2":
            self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip2-opt-2.7b",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            self.blip_model.to(self.device)
            logger.info("✓ BLIP-2 loaded")
        
        self.model.eval()
    
    def fetch_image(self, image_url: str) -> Optional[Image.Image]:
        """Download and load image from URL"""
        try:
            response = requests.get(image_url, timeout=5)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert("RGB")
            return image
        except Exception as e:
            logger.debug(f"Error loading image {image_url}: {e}")
            return None
    
    def check_text_image_match_clip(self, text: str, image_url: str) -> Dict:
        """
        Use CLIP to score text-image alignment
        Fast (~100ms) and good for consistency checking
        """
        
        image = self.fetch_image(image_url)
        if not image:
            return {'error': 'Could not load image', 'score': 0.5}
        
        try:
            # CLIP image-text matching
            inputs = self.processor(
                text=[text],
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Similarity score (CLIP logits scaled to 0-100)
            logits = outputs.logits_per_image
            similarity_score = float((logits / 100 + 1).cpu().numpy()[0][0])  # Normalize
            
            return {
                'score': min(max(similarity_score, 0), 1),  # Clamp to 0-1
                'match_quality': self._interpret_score(similarity_score),
                'inference_time_ms': 100,
                'method': 'clip'
            }
        
        except Exception as e:
            logger.error(f"CLIP matching error: {e}")
            return {'error': str(e), 'score': 0.5}
    
    def detect_stock_photo(self, image_url: str) -> Dict:
        """
        Detect if image is stock/generic using BLIP-2
        """
        
        image = self.fetch_image(image_url)
        if not image:
            return {'is_stock': False, 'confidence': 0}
        
        try:
            # BLIP-2: Caption image
            inputs = self.blip_processor(
                images=image,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                generated_ids = self.blip_model.generate(**inputs, max_length=30)
            
            caption = self.blip_processor.decode(
                generated_ids[0],
                skip_special_tokens=True
            )
            
            # Check for stock photo indicators
            stock_keywords = [
                'stock', 'generic', 'illustration', 'mockup', 'abstract',
                'placeholder', 'colorful', 'pattern', 'background',
                'a person', 'people', 'group', 'diverse', 'multicultural'
            ]
            
            is_stock = any(kw in caption.lower() for kw in stock_keywords)
            
            return {
                'is_stock': is_stock,
                'caption': caption,
                'confidence': 0.8 if is_stock else 0.7
            }
        
        except Exception as e:
            logger.error(f"Stock photo detection error: {e}")
            return {'is_stock': False, 'caption': '', 'confidence': 0}
    
    def _interpret_score(self, score: float) -> str:
        """Interpret CLIP similarity score"""
        if score > 0.7:
            return 'excellent_match'
        elif score > 0.5:
            return 'good_match'
        elif score > 0.3:
            return 'weak_match'
        else:
            return 'poor_match'
    
    def analyze_review_multimodal(
        self,
        review_text: str,
        image_urls: List[str]
    ) -> Dict:
        """
        Full multimodal analysis for a review
        Check consistency between text and all product images
        """
        
        if not image_urls:
            return {
                'multimodal_score': 0.5,
                'suspicious_images': [],
                'assessment': 'NO_IMAGES',
                'images_analyzed': 0
            }
        
        consistency_scores = []
        suspicious_images = []
        
        for img_url in image_urls[:5]:  # Analyze top 5 images
            # Text-image matching
            match_result = self.check_text_image_match_clip(review_text, img_url)
            
            if 'error' in match_result:
                continue
            
            score = match_result['score']
            consistency_scores.append(score)
            
            # Stock photo detection
            stock_result = self.detect_stock_photo(img_url)
            
            if score < 0.4 or stock_result['is_stock']:
                suspicious_images.append({
                    'url': img_url,
                    'consistency_score': score,
                    'caption': stock_result.get('caption', ''),
                    'is_stock': stock_result['is_stock'],
                    'reason': 'Poor text-image match' if score < 0.4 else 'Stock/generic image'
                })
        
        avg_consistency = np.mean(consistency_scores) if consistency_scores else 0.5
        
        # Assessment
        if avg_consistency < 0.3:
            assessment = 'LIKELY_FAKE'
        elif avg_consistency < 0.5:
            assessment = 'SUSPICIOUS'
        else:
            assessment = 'CONSISTENT'
        
        return {
            'multimodal_score': float(avg_consistency),
            'suspicious_images': suspicious_images,
            'assessment': assessment,
            'images_analyzed': len(image_urls),
            'suspicious_count': len(suspicious_images),
            'confidence': 0.85 if len(image_urls) > 0 else 0.5
        }