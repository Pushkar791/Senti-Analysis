import asyncio
import time
import json
from datetime import datetime
from typing import List, Dict
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sentiment_analyzer_vercel import AdvancedSentimentAnalyzer
from database import SentimentDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Real-time Sentiment Analysis API",
    description="Advanced sentiment analysis system with WebSocket support",
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

# Initialize components
analyzer = AdvancedSentimentAnalyzer()
db = SentimentDatabase()

# Pydantic models
class SentimentRequest(BaseModel):
    text: str
    save_to_db: bool = True

@app.get("/")
async def home():
    """Basic home endpoint"""
    return {"message": "Sentiment Analysis API is running!", "status": "healthy"}

@app.post("/api/analyze")
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment of a single text"""
    start_time = time.time()
    
    try:
        # Perform sentiment analysis
        result = await analyzer.analyze_comprehensive(request.text)
        processing_time = time.time() - start_time
        
        # Add processing time to result
        result['processing_time'] = round(processing_time, 3)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Sentiment Analysis API...")
    logger.info("Initializing database...")
    await db.initialize_database()
    logger.info("API ready!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_debug:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
