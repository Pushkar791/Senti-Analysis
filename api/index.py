import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import our modules
try:
    from sentiment_analyzer_vercel import AdvancedSentimentAnalyzer
    from database import SentimentDatabase
except ImportError:
    # Fallback for Vercel
    import importlib.util
    
    # Load sentiment_analyzer_vercel
    spec = importlib.util.spec_from_file_location("sentiment_analyzer_vercel", 
        os.path.join(os.path.dirname(__file__), "..", "backend", "sentiment_analyzer_vercel.py"))
    sentiment_analyzer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sentiment_analyzer_module)
    AdvancedSentimentAnalyzer = sentiment_analyzer_module.AdvancedSentimentAnalyzer
    
    # Load database
    spec = importlib.util.spec_from_file_location("database", 
        os.path.join(os.path.dirname(__file__), "..", "backend", "database.py"))
    database_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database_module)
    SentimentDatabase = database_module.SentimentDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Real-time Sentiment Analysis API",
    description="Advanced sentiment analysis system optimized for Vercel",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates (adjust paths for Vercel)
try:
    static_path = os.path.join(os.path.dirname(__file__), "..", "static")
    templates_path = os.path.join(os.path.dirname(__file__), "..", "templates")
    
    if os.path.exists(static_path):
        app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    if os.path.exists(templates_path):
        templates = Jinja2Templates(directory=templates_path)
    else:
        templates = None
except Exception as e:
    logger.warning(f"Could not mount static files or templates: {e}")
    templates = None

# Initialize components (with error handling for Vercel)
# Also keep lightweight in-memory activity tracking for "Active Users" metric
try:
    analyzer = AdvancedSentimentAnalyzer()
    db = SentimentDatabase(db_path="/tmp/sentiment_data.db")  # Use /tmp for Vercel
    logger.info("Components initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    analyzer = None
    db = None

# In-memory recent activity tracker (per serverless instance)
recent_activity: dict = {}

def record_activity(ip: str):
    try:
        if not ip:
            return
        recent_activity[ip] = datetime.utcnow()
    except Exception:
        pass

def get_active_users(window_seconds: int = 300) -> int:
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    # prune old entries
    stale_keys = [k for k, ts in recent_activity.items() if ts < cutoff]
    for k in stale_keys:
        recent_activity.pop(k, None)
    return len(recent_activity)

# Pydantic models
class SentimentRequest(BaseModel):
    text: str
    save_to_db: bool = True

class BatchSentimentRequest(BaseModel):
    texts: List[str]
    save_to_db: bool = True

# Routes
@app.get("/")
async def home(request: Request):
    """Serve the main HTML page"""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        # Fallback HTML for Vercel
        return JSONResponse({
            "message": "Sentiment Analysis API is running!",
            "endpoints": {
                "analyze": "/api/analyze",
                "batch_analyze": "/api/analyze-batch",
                "analytics": "/api/analytics",
                "health": "/api/health"
            }
        })

@app.post("/api/analyze")
async def analyze_sentiment(request: SentimentRequest, req: Request, background_tasks: BackgroundTasks):
    """Analyze sentiment of a single text"""
    if not analyzer:
        raise HTTPException(status_code=500, detail="Sentiment analyzer not available")
    
    start_time = time.time()
    
    try:
        # Perform sentiment analysis
        result = await analyzer.analyze_comprehensive(request.text)
        processing_time = time.time() - start_time
        
        # Add processing time to result
        result['processing_time'] = round(processing_time, 3)
        
        # Record activity for "Active Users" metric
        client_ip = getattr(req.client, 'host', 'unknown')
        record_activity(client_ip)

        # Save to database if available and requested
        if request.save_to_db and db and 'error' not in result:
            user_agent = req.headers.get('user-agent', '')
            
            try:
                background_tasks.add_task(
                    db.save_review, 
                    result, 
                    client_ip, 
                    user_agent
                )
            except Exception as db_error:
                logger.warning(f"Database save failed: {db_error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-batch")
async def analyze_batch_sentiment(request: BatchSentimentRequest, req: Request, background_tasks: BackgroundTasks):
    """Analyze sentiment of multiple texts"""
    if not analyzer:
        raise HTTPException(status_code=500, detail="Sentiment analyzer not available")
    
    start_time = time.time()
    
    try:
        # Perform batch analysis
        results = await analyzer.analyze_batch(request.texts)
        processing_time = time.time() - start_time
        
        # Add processing time
        batch_result = {
            'results': results,
            'batch_size': len(request.texts),
            'processing_time': round(processing_time, 3),
            'avg_time_per_text': round(processing_time / len(request.texts), 3) if request.texts else 0
        }
        
        # Record activity
        client_ip = getattr(req.client, 'host', 'unknown')
        record_activity(client_ip)

        # Save to database if available and requested
        if request.save_to_db and db:
            user_agent = req.headers.get('user-agent', '')
            
            try:
                for result in results:
                    if 'error' not in result:
                        background_tasks.add_task(db.save_review, result, client_ip, user_agent)
            except Exception as db_error:
                logger.warning(f"Batch database save failed: {db_error}")
        
        return batch_result
        
    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics")
async def get_analytics(days: int = 7):
    """Get analytics summary"""
    active_users = get_active_users()
    if not db:
        return {
            'summary': {
                'total_reviews': 0,
                'reviews_today': 0,
                'average_confidence': 0,
                'sentiment_distribution': {'counts': {}, 'percentages': {}, 'total': 0},
                'emotion_analysis': {'emotion_averages': {}},
                'active_users': active_users
            },
            'trends': {},
            'recent_reviews': []
        }
    
    try:
        summary = await db.get_analytics_summary()
        trends = await db.get_sentiment_trends(days)
        recent_reviews = await db.get_recent_reviews(limit=50)
        
        return {
            'summary': summary,
            'trends': trends,
            'recent_reviews': recent_reviews
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        # Return empty analytics instead of failing
        return {
            'summary': {
                'total_reviews': 0,
                'reviews_today': 0,
                'average_confidence': 0,
                'sentiment_distribution': {'counts': {}, 'percentages': {}, 'total': 0},
                'emotion_analysis': {'emotion_averages': {}},
                'active_users': active_users
            },
            'trends': {},
            'recent_reviews': []
        }

@app.get("/api/recent-reviews")
async def get_recent_reviews(limit: int = 100):
    """Get recent sentiment analysis results"""
    if not db:
        return {'reviews': []}
    
    try:
        reviews = await db.get_recent_reviews(limit)
        return {'reviews': reviews}
    except Exception as e:
        logger.error(f"Error getting recent reviews: {e}")
        return {'reviews': []}

@app.get("/api/sentiment-distribution")
async def get_sentiment_distribution(days: int = 7):
    """Get sentiment distribution"""
    if not db:
        return {'counts': {}, 'percentages': {}, 'total': 0, 'period_days': days}
    
    try:
        distribution = await db.get_sentiment_distribution(days)
        return distribution
    except Exception as e:
        logger.error(f"Error getting sentiment distribution: {e}")
        return {'counts': {}, 'percentages': {}, 'total': 0, 'period_days': days}

@app.get("/api/emotion-analysis")
async def get_emotion_analysis(days: int = 7):
    """Get emotion analysis"""
    if not db:
        return {'emotion_averages': {}, 'total_reviews': 0, 'period_days': days}
    
    try:
        emotions = await db.get_emotion_analysis(days)
        return emotions
    except Exception as e:
        logger.error(f"Error getting emotion analysis: {e}")
        return {'emotion_averages': {}, 'total_reviews': 0, 'period_days': days}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'analyzer_available': analyzer is not None,
        'database_available': db is not None,
        'environment': 'vercel'
    }

# Startup event (modified for serverless)
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Sentiment Analysis API on Vercel...")
    if db:
        try:
            await db.initialize_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
    logger.info("API ready!")

# Export the app for Vercel
handler = app
