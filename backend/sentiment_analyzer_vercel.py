import asyncio
import logging
from typing import Dict, List, Tuple
from datetime import datetime
import re

# NLP Libraries
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except:
    pass

class AdvancedSentimentAnalyzer:
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text
    
    def analyze_with_vader(self, text: str) -> Dict:
        """Analyze sentiment using VADER (fast, good for social media text)"""
        scores = self.vader_analyzer.polarity_scores(text)
        
        # Determine sentiment label
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
            
        return {
            'sentiment': sentiment,
            'confidence': abs(compound),
            'scores': scores,
            'method': 'VADER'
        }
    
    def get_emotion_indicators(self, text: str) -> Dict[str, float]:
        """Extract emotion indicators from text"""
        emotion_keywords = {
            'joy': ['happy', 'joy', 'excited', 'delighted', 'pleased', 'satisfied', 'amazing', 'wonderful', 'excellent', 'fantastic'],
            'anger': ['angry', 'frustrated', 'annoyed', 'furious', 'irritated', 'outraged', 'terrible', 'awful', 'horrible', 'disgusting'],
            'sadness': ['sad', 'disappointed', 'depressed', 'upset', 'heartbroken', 'miserable', 'poor', 'bad', 'worse', 'worst'],
            'fear': ['afraid', 'scared', 'worried', 'anxious', 'nervous', 'concerned', 'uncertain', 'doubtful'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'unexpected', 'wow', 'incredible'],
            'disgust': ['disgusted', 'revolting', 'repulsive', 'gross', 'nasty', 'yuck']
        }
        
        text_lower = text.lower()
        emotions = {}
        
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            emotions[emotion] = score / len(keywords) if keywords else 0
            
        return emotions
    
    def calculate_text_metrics(self, text: str) -> Dict:
        """Calculate various text metrics"""
        words = text.split()
        sentences = text.split('.')
        
        # Compute average word length without numpy to keep dependencies light
        avg_word_length = (sum(len(word) for word in words) / len(words)) if words else 0
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': avg_word_length,
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'caps_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0
        }
    
    async def analyze_comprehensive(self, text: str) -> Dict:
        """Comprehensive sentiment analysis using VADER only (Vercel optimized)"""
        if not text or not text.strip():
            return {
                'error': 'Empty text provided',
                'timestamp': datetime.now().isoformat()
            }
        
        # Preprocess text
        clean_text = self.preprocess_text(text)
        
        # Run analyses
        vader_result = self.analyze_with_vader(clean_text)
        emotions = self.get_emotion_indicators(clean_text)
        metrics = self.calculate_text_metrics(text)
        
        # For Vercel deployment, use only VADER results
        final_sentiment = vader_result['sentiment']
        confidence = vader_result['confidence']
        
        return {
            'text': text,
            'clean_text': clean_text,
            'sentiment': final_sentiment,
            'confidence': round(confidence, 3),
            'vader_analysis': vader_result,
            'transformer_analysis': None,  # Not available in Vercel
            'emotions': emotions,
            'text_metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    async def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts efficiently"""
        tasks = [self.analyze_comprehensive(text) for text in texts]
        return await asyncio.gather(*tasks)
