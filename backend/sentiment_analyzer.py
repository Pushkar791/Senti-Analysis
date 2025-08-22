import asyncio
import logging
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
import re

# NLP Libraries
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

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
        self.setup_transformers_model()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def setup_transformers_model(self):
        """Initialize HuggingFace transformer model for more accurate analysis"""
        try:
            # Using a lightweight but accurate model
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.transformer_pipeline = pipeline(
                "sentiment-analysis", 
                model=self.model, 
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                max_length=512,
                truncation=True
            )
            self.logger.info("Transformer model loaded successfully")
        except Exception as e:
            self.logger.warning(f"Could not load transformer model: {e}")
            self.transformer_pipeline = None
    
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
    
    def analyze_with_transformer(self, text: str) -> Dict:
        """Analyze sentiment using transformer model (more accurate)"""
        if not self.transformer_pipeline:
            return None
            
        try:
            result = self.transformer_pipeline(text)[0]
            
            # Map labels to consistent format
            label_mapping = {
                'LABEL_0': 'negative',
                'LABEL_1': 'neutral', 
                'LABEL_2': 'positive',
                'NEGATIVE': 'negative',
                'NEUTRAL': 'neutral',
                'POSITIVE': 'positive'
            }
            
            sentiment = label_mapping.get(result['label'].upper(), result['label'].lower())
            
            return {
                'sentiment': sentiment,
                'confidence': result['score'],
                'method': 'Transformer'
            }
        except Exception as e:
            self.logger.error(f"Transformer analysis failed: {e}")
            return None
    
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
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': np.mean([len(word) for word in words]) if words else 0,
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'caps_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0
        }
    
    async def analyze_comprehensive(self, text: str) -> Dict:
        """Comprehensive sentiment analysis using multiple methods"""
        if not text or not text.strip():
            return {
                'error': 'Empty text provided',
                'timestamp': datetime.now().isoformat()
            }
        
        # Preprocess text
        clean_text = self.preprocess_text(text)
        
        # Run analyses
        vader_result = self.analyze_with_vader(clean_text)
        transformer_result = self.analyze_with_transformer(clean_text)
        emotions = self.get_emotion_indicators(clean_text)
        metrics = self.calculate_text_metrics(text)
        
        # Ensemble result - combine VADER and transformer if available
        if transformer_result:
            # Weight transformer more heavily for final decision
            if vader_result['sentiment'] == transformer_result['sentiment']:
                final_sentiment = vader_result['sentiment']
                confidence = (vader_result['confidence'] + transformer_result['confidence']) / 2
            else:
                # Use transformer result with higher weight
                final_sentiment = transformer_result['sentiment']
                confidence = transformer_result['confidence'] * 0.7 + vader_result['confidence'] * 0.3
        else:
            final_sentiment = vader_result['sentiment']
            confidence = vader_result['confidence']
        
        return {
            'text': text,
            'clean_text': clean_text,
            'sentiment': final_sentiment,
            'confidence': round(confidence, 3),
            'vader_analysis': vader_result,
            'transformer_analysis': transformer_result,
            'emotions': emotions,
            'text_metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    async def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts efficiently"""
        tasks = [self.analyze_comprehensive(text) for text in texts]
        return await asyncio.gather(*tasks)
