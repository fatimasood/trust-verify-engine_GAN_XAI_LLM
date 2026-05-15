import re
from src.utils import logger

class FreeFactChecker:
    def verify_claims(self, text: str) -> dict:
        # Very basic claim extraction (numbers, dates, statements)
        claims = []
        sentences = re.split(r'[.!?]', text)
        for sent in sentences:
            if len(sent.strip()) > 20 and any(word in sent.lower() for word in ['best', 'worst', '100%', 'always', 'never']):
                claims.append({'text': sent.strip(), 'verification_status': 'Unverified', 'evidence': 'Manual check required'})
        return {'claims': claims[:3]}