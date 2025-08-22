import asyncio
import time
import json
from datetime import datetime
from typing import List, Dict
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

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

# Mount static files and templates using absolute paths derived from this file location
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Initialize components
analyzer = AdvancedSentimentAnalyzer()
db = SentimentDatabase()

# Pydantic models
class SentimentRequest(BaseModel):
    text: str
    save_to_db: bool = True

class BatchSentimentRequest(BaseModel):
    texts: List[str]
    save_to_db: bool = True

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Routes
@app.get("/")
async def home(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/analyze")
async def analyze_sentiment(request: SentimentRequest, req: Request, background_tasks: BackgroundTasks):
    """Analyze sentiment of a single text"""
    start_time = time.time()
    
    try:
        # Perform sentiment analysis
        result = await analyzer.analyze_comprehensive(request.text)
        processing_time = time.time() - start_time
        
        # Add processing time to result
        result['processing_time'] = round(processing_time, 3)
        
        # Save to database if requested
        if request.save_to_db and 'error' not in result:
            client_ip = req.client.host
            user_agent = req.headers.get('user-agent', '')
            
            background_tasks.add_task(
                db.save_review, 
                result, 
                client_ip, 
                user_agent
            )
            
            # Broadcast to WebSocket connections
            broadcast_message = {
                'type': 'new_analysis',
                'data': {
                    'sentiment': result['sentiment'],
                    'confidence': result['confidence'],
                    'text_preview': request.text[:100] + ('...' if len(request.text) > 100 else ''),
                    'timestamp': result['timestamp']
                }
            }
            background_tasks.add_task(manager.broadcast, json.dumps(broadcast_message))
        
        return result
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-batch")
async def analyze_batch_sentiment(request: BatchSentimentRequest, req: Request, background_tasks: BackgroundTasks):
    """Analyze sentiment of multiple texts"""
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
        
        # Save to database if requested
        if request.save_to_db:
            client_ip = req.client.host
            user_agent = req.headers.get('user-agent', '')
            
            for result in results:
                if 'error' not in result:
                    background_tasks.add_task(db.save_review, result, client_ip, user_agent)
        
        return batch_result
        
    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics")
async def get_analytics(days: int = 7):
    """Get analytics summary"""
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-reviews")
async def get_recent_reviews(limit: int = 100):
    """Get recent sentiment analysis results"""
    try:
        reviews = await db.get_recent_reviews(limit)
        return {'reviews': reviews}
    except Exception as e:
        logger.error(f"Error getting recent reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sentiment-distribution")
async def get_sentiment_distribution(days: int = 7):
    """Get sentiment distribution"""
    try:
        distribution = await db.get_sentiment_distribution(days)
        return distribution
    except Exception as e:
        logger.error(f"Error getting sentiment distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emotion-analysis")
async def get_emotion_analysis(days: int = 7):
    """Get emotion analysis"""
    try:
        emotions = await db.get_emotion_analysis(days)
        return emotions
    except Exception as e:
        logger.error(f"Error getting emotion analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    
    try:
        # Send initial analytics data
        initial_data = {
            'type': 'initial_data',
            'data': await db.get_analytics_summary()
        }
        await manager.send_personal_message(json.dumps(initial_data), websocket)
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'analyze_text':
                # Real-time sentiment analysis
                text = message['data']['text']
                
                if text.strip():
                    start_time = time.time()
                    result = await analyzer.analyze_comprehensive(text)
                    processing_time = time.time() - start_time
                    
                    result['processing_time'] = round(processing_time, 3)
                    
                    # Send result back to client
                    response = {
                        'type': 'analysis_result',
                        'data': result
                    }
                    await manager.send_personal_message(json.dumps(response), websocket)
                    
                    # Save to database
                    if 'error' not in result:
                        await db.save_review(result)
                        
                        # Broadcast to all connected clients
                        broadcast_message = {
                            'type': 'new_analysis',
                            'data': {
                                'sentiment': result['sentiment'],
                                'confidence': result['confidence'],
                                'text_preview': text[:100] + ('...' if len(text) > 100 else ''),
                                'timestamp': result['timestamp']
                            }
                        }
                        await manager.broadcast(json.dumps(broadcast_message))
                        
            elif message['type'] == 'get_analytics':
                # Send updated analytics
                analytics = await db.get_analytics_summary()
                response = {
                    'type': 'analytics_update',
                    'data': analytics
                }
                await manager.send_personal_message(json.dumps(response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_websockets': len(manager.active_connections)
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
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
