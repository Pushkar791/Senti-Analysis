import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import aiosqlite
from pathlib import Path

class SentimentDatabase:
    def __init__(self, db_path: str = "data/sentiment_data.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(exist_ok=True)
    
    async def initialize_database(self):
        """Initialize the database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create reviews table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    clean_text TEXT,
                    sentiment TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    vader_scores TEXT,
                    transformer_scores TEXT,
                    emotions TEXT,
                    text_metrics TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """)
            
            # Create sentiment_stats table for aggregated data
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    sentiment TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    avg_confidence REAL NOT NULL,
                    UNIQUE(date, sentiment)
                )
            """)
            
            # Create performance metrics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processing_time REAL,
                    model_used TEXT,
                    success BOOLEAN
                )
            """)
            
            # Create suggestions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    impact_score INTEGER NOT NULL,
                    effort_estimate TEXT NOT NULL,
                    expected_outcome TEXT,
                    action_items TEXT,
                    status TEXT DEFAULT 'pending',
                    generated_at DATETIME NOT NULL,
                    analysis_period INTEGER NOT NULL,
                    implemented_at DATETIME,
                    dismissed_at DATETIME,
                    notes TEXT
                )
            """)
            
            # Create suggestion feedback table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS suggestion_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suggestion_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    feedback TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    FOREIGN KEY (suggestion_id) REFERENCES suggestions (id)
                )
            """)
            
            await db.commit()
    
    async def save_review(self, analysis_result: Dict, ip_address: str = None, user_agent: str = None):
        """Save a sentiment analysis result to the database"""
        if 'error' in analysis_result:
            return None
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO reviews (
                    text, clean_text, sentiment, confidence,
                    vader_scores, transformer_scores, emotions, text_metrics,
                    timestamp, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_result['text'],
                analysis_result['clean_text'],
                analysis_result['sentiment'],
                analysis_result['confidence'],
                json.dumps(analysis_result.get('vader_analysis', {})),
                json.dumps(analysis_result.get('transformer_analysis', {})),
                json.dumps(analysis_result['emotions']),
                json.dumps(analysis_result['text_metrics']),
                analysis_result['timestamp'],
                ip_address,
                user_agent
            ))
            
            review_id = cursor.lastrowid
            await db.commit()
            
            # Update daily stats
            await self.update_daily_stats(analysis_result['sentiment'], analysis_result['confidence'])
            
            return review_id
    
    async def update_daily_stats(self, sentiment: str, confidence: float):
        """Update daily sentiment statistics"""
        today = datetime.now().date()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Check if stat exists for today and sentiment
            cursor = await db.execute(
                "SELECT count, avg_confidence FROM sentiment_stats WHERE date = ? AND sentiment = ?",
                (today, sentiment)
            )
            result = await cursor.fetchone()
            
            if result:
                # Update existing stat
                new_count = result[0] + 1
                new_avg_confidence = (result[1] * result[0] + confidence) / new_count
                
                await db.execute("""
                    UPDATE sentiment_stats 
                    SET count = ?, avg_confidence = ? 
                    WHERE date = ? AND sentiment = ?
                """, (new_count, new_avg_confidence, today, sentiment))
            else:
                # Create new stat entry
                await db.execute("""
                    INSERT INTO sentiment_stats (date, sentiment, count, avg_confidence)
                    VALUES (?, ?, 1, ?)
                """, (today, sentiment, confidence))
            
            await db.commit()
    
    async def get_recent_reviews(self, limit: int = 100) -> List[Dict]:
        """Get recent sentiment analysis results"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT text, sentiment, confidence, emotions, timestamp
                FROM reviews 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            results = await cursor.fetchall()
            
            return [
                {
                    'text': row[0],
                    'sentiment': row[1],
                    'confidence': row[2],
                    'emotions': json.loads(row[3]) if row[3] else {},
                    'timestamp': row[4]
                }
                for row in results
            ]
    
    async def get_sentiment_distribution(self, days: int = 7) -> Dict:
        """Get sentiment distribution over the last N days"""
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT sentiment, SUM(count) as total_count
                FROM sentiment_stats 
                WHERE date >= ?
                GROUP BY sentiment
            """, (start_date,))
            
            results = await cursor.fetchall()
            
            distribution = {row[0]: row[1] for row in results}
            total = sum(distribution.values())
            
            if total > 0:
                percentages = {k: round((v / total) * 100, 2) for k, v in distribution.items()}
            else:
                percentages = {}
            
            return {
                'counts': distribution,
                'percentages': percentages,
                'total': total,
                'period_days': days
            }
    
    async def get_sentiment_trends(self, days: int = 30) -> Dict:
        """Get sentiment trends over time"""
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT date, sentiment, count, avg_confidence
                FROM sentiment_stats 
                WHERE date >= ?
                ORDER BY date, sentiment
            """, (start_date,))
            
            results = await cursor.fetchall()
            
            trends = {}
            for row in results:
                date_str = row[0]
                if date_str not in trends:
                    trends[date_str] = {}
                
                trends[date_str][row[1]] = {
                    'count': row[2],
                    'avg_confidence': row[3]
                }
            
            return trends
    
    async def get_emotion_analysis(self, days: int = 7) -> Dict:
        """Get emotion analysis for the last N days"""
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT emotions FROM reviews 
                WHERE DATE(timestamp) >= ?
            """, (start_date,))
            
            results = await cursor.fetchall()
            
            emotion_totals = {}
            count = 0
            
            for row in results:
                if row[0]:
                    emotions = json.loads(row[0])
                    count += 1
                    for emotion, score in emotions.items():
                        if emotion not in emotion_totals:
                            emotion_totals[emotion] = 0
                        emotion_totals[emotion] += score
            
            if count > 0:
                emotion_averages = {k: round(v / count, 3) for k, v in emotion_totals.items()}
            else:
                emotion_averages = {}
            
            return {
                'emotion_averages': emotion_averages,
                'total_reviews': count,
                'period_days': days
            }
    
    async def get_analytics_summary(self) -> Dict:
        """Get comprehensive analytics summary"""
        # Get basic stats
        async with aiosqlite.connect(self.db_path) as db:
            # Total reviews
            cursor = await db.execute("SELECT COUNT(*) FROM reviews")
            total_reviews = (await cursor.fetchone())[0]
            
            # Reviews today
            today = datetime.now().date()
            cursor = await db.execute(
                "SELECT COUNT(*) FROM reviews WHERE DATE(timestamp) = ?", 
                (today,)
            )
            reviews_today = (await cursor.fetchone())[0]
            
            # Average confidence
            cursor = await db.execute("SELECT AVG(confidence) FROM reviews")
            avg_confidence = (await cursor.fetchone())[0] or 0
        
        # Get distribution and trends
        distribution = await self.get_sentiment_distribution(7)
        emotion_analysis = await self.get_emotion_analysis(7)
        
        return {
            'total_reviews': total_reviews,
            'reviews_today': reviews_today,
            'average_confidence': round(avg_confidence, 3),
            'sentiment_distribution': distribution,
            'emotion_analysis': emotion_analysis,
            'generated_at': datetime.now().isoformat()
        }
    
    # Suggestion Management Methods
    
    async def save_suggestions(self, suggestions: List[Dict]) -> int:
        """Save multiple suggestions to the database"""
        if not suggestions:
            return 0
            
        saved_count = 0
        async with aiosqlite.connect(self.db_path) as db:
            for suggestion in suggestions:
                try:
                    await db.execute("""
                        INSERT OR REPLACE INTO suggestions (
                            id, title, description, category, priority,
                            impact_score, effort_estimate, expected_outcome,
                            action_items, generated_at, analysis_period
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        suggestion['id'],
                        suggestion['title'],
                        suggestion['description'],
                        suggestion['category'],
                        suggestion['priority'],
                        suggestion['impact_score'],
                        suggestion['effort_estimate'],
                        suggestion.get('expected_outcome', ''),
                        json.dumps(suggestion.get('action_items', [])),
                        suggestion['generated_at'],
                        suggestion['analysis_period']
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving suggestion {suggestion.get('id', 'unknown')}: {e}")
                    
            await db.commit()
            
        return saved_count
    
    async def get_suggestions(self, status: Optional[str] = None, category: Optional[str] = None, 
                             limit: int = 50) -> List[Dict]:
        """Get suggestions with optional filtering"""
        query = """
            SELECT id, title, description, category, priority, impact_score,
                   effort_estimate, expected_outcome, action_items, status,
                   generated_at, analysis_period, implemented_at, dismissed_at, notes
            FROM suggestions
        """
        
        conditions = []
        params = []
        
        if status:
            conditions.append("status = ?")
            params.append(status)
            
        if category:
            conditions.append("category = ?")
            params.append(category)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY priority DESC, impact_score DESC, generated_at DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            results = await cursor.fetchall()
            
            suggestions = []
            for row in results:
                suggestion = {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'category': row[3],
                    'priority': row[4],
                    'impact_score': row[5],
                    'effort_estimate': row[6],
                    'expected_outcome': row[7],
                    'action_items': json.loads(row[8]) if row[8] else [],
                    'status': row[9],
                    'generated_at': row[10],
                    'analysis_period': row[11],
                    'implemented_at': row[12],
                    'dismissed_at': row[13],
                    'notes': row[14]
                }
                suggestions.append(suggestion)
                
            return suggestions
    
    async def update_suggestion_status(self, suggestion_id: str, status: str, 
                                     notes: Optional[str] = None, ip_address: Optional[str] = None) -> bool:
        """Update the status of a suggestion"""
        valid_statuses = ['pending', 'implemented', 'dismissed', 'in_progress']
        if status not in valid_statuses:
            return False
            
        async with aiosqlite.connect(self.db_path) as db:
            # Update suggestion status
            if status == 'implemented':
                await db.execute("""
                    UPDATE suggestions 
                    SET status = ?, implemented_at = ?, notes = ?
                    WHERE id = ?
                """, (status, datetime.now().isoformat(), notes or '', suggestion_id))
            elif status == 'dismissed':
                await db.execute("""
                    UPDATE suggestions 
                    SET status = ?, dismissed_at = ?, notes = ?
                    WHERE id = ?
                """, (status, datetime.now().isoformat(), notes or '', suggestion_id))
            else:
                await db.execute("""
                    UPDATE suggestions 
                    SET status = ?, notes = ?
                    WHERE id = ?
                """, (status, notes or '', suggestion_id))
            
            # Log the action in feedback table
            await db.execute("""
                INSERT INTO suggestion_feedback (suggestion_id, action, feedback, ip_address)
                VALUES (?, ?, ?, ?)
            """, (suggestion_id, status, notes or '', ip_address))
            
            await db.commit()
            
            # Check if update was successful
            cursor = await db.execute("SELECT changes()")
            changes = (await cursor.fetchone())[0]
            
            return changes > 0
    
    async def get_suggestion_stats(self) -> Dict:
        """Get statistics about suggestions"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total suggestions
            cursor = await db.execute("SELECT COUNT(*) FROM suggestions")
            total = (await cursor.fetchone())[0]
            
            # By status
            cursor = await db.execute("""
                SELECT status, COUNT(*) 
                FROM suggestions 
                GROUP BY status
            """)
            status_counts = dict(await cursor.fetchall())
            
            # By category
            cursor = await db.execute("""
                SELECT category, COUNT(*) 
                FROM suggestions 
                GROUP BY category 
                ORDER BY COUNT(*) DESC
            """)
            category_counts = dict(await cursor.fetchall())
            
            # By priority
            cursor = await db.execute("""
                SELECT priority, COUNT(*) 
                FROM suggestions 
                GROUP BY priority
            """)
            priority_counts = dict(await cursor.fetchall())
            
            # Recent activity
            cursor = await db.execute("""
                SELECT COUNT(*) 
                FROM suggestions 
                WHERE DATE(generated_at) >= DATE('now', '-7 days')
            """)
            recent_suggestions = (await cursor.fetchone())[0]
            
            return {
                'total_suggestions': total,
                'status_breakdown': status_counts,
                'category_breakdown': category_counts,
                'priority_breakdown': priority_counts,
                'recent_suggestions': recent_suggestions,
                'implementation_rate': round(
                    (status_counts.get('implemented', 0) / total * 100) if total > 0 else 0, 1
                )
            }
    
    async def delete_old_suggestions(self, days: int = 90) -> int:
        """Delete suggestions older than specified days (cleanup)"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Delete old suggestions
            cursor = await db.execute("""
                DELETE FROM suggestions 
                WHERE generated_at < ? AND status IN ('dismissed', 'implemented')
            """, (cutoff_date,))
            
            await db.commit()
            
            return cursor.rowcount
