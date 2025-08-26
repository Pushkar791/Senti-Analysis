#!/usr/bin/env python3
"""
Script to add sample data to the sentiment analysis database
This helps test the charts and analytics features
"""

import asyncio
import json
from datetime import datetime, timedelta
import random

from database import SentimentDatabase
from sentiment_analyzer_vercel import AdvancedSentimentAnalyzer

# Sample reviews with different sentiments
SAMPLE_REVIEWS = [
    # Positive reviews
    "This product is absolutely amazing! I love how easy it is to use and the quality is outstanding. Highly recommended!",
    "Exceptional service and fantastic product quality! The team went above and beyond to ensure customer satisfaction. Five stars!",
    "Outstanding experience! Fast delivery, great customer service, and the product exceeded my expectations.",
    "Perfect! Exactly what I was looking for. Great value for money and excellent quality.",
    "Wonderful product! Easy to use, high quality, and fantastic customer support.",
    "Best purchase I've made in a long time! Highly recommend to anyone looking for quality.",
    "Amazing! Fast shipping, great packaging, and the product is exactly as described.",
    "Excellent quality and performance. Very satisfied with this purchase.",
    "Great product, great service, great experience overall!",
    "Love it! Perfect size, excellent quality, and arrived quickly.",
    
    # Negative reviews  
    "I'm really disappointed with this purchase. The quality is poor and it doesn't work as advertised. Waste of money.",
    "Terrible experience. The product arrived damaged and customer service was unhelpful. Will not buy again.",
    "Poor quality product. Broke after just a few uses. Very disappointed.",
    "Overpriced and underwhelming. Not worth the money at all.",
    "Horrible customer service. Took forever to get a response and they weren't helpful.",
    "The product is cheap and flimsy. Definitely not as advertised.",
    "Very disappointed. Product arrived late and was not as described.",
    "Waste of money. Product stopped working after a week.",
    "Terrible quality. Looks nothing like the pictures. Very upset.",
    "Not recommended. Poor build quality and terrible customer support.",
    
    # Neutral reviews
    "The product is okay, nothing special. It does what it's supposed to do but there are better alternatives available.",
    "Pretty good value for money. Some minor issues but overall satisfied with the purchase. Would consider buying again.",
    "Average product. Works as expected but nothing outstanding about it.",
    "It's fine. Does the job but could be better quality for the price.",
    "Decent product. Not bad but not amazing either. Gets the job done.",
    "Acceptable quality. Some room for improvement but generally satisfied.",
    "Standard product. Works as advertised but nothing special.",
    "Fair quality for the price. Would be nice to have better materials.",
    "It's okay. Not the best but not the worst I've bought.",
    "Mediocre. Works fine but expected more for the price."
]

async def add_sample_data():
    """Add sample sentiment analysis data to the database"""
    print("🚀 Starting to add sample data...")
    
    # Initialize components
    db = SentimentDatabase()
    analyzer = AdvancedSentimentAnalyzer()
    
    # Initialize database
    await db.initialize_database()
    print("✅ Database initialized")
    
    added_count = 0
    
    # Add reviews for the past 14 days
    for i in range(14):
        # Create date for past days
        date_offset = datetime.now() - timedelta(days=i)
        
        # Random number of reviews per day (3-8)
        daily_reviews = random.randint(3, 8)
        print(f"📅 Adding {daily_reviews} reviews for {date_offset.strftime('%Y-%m-%d')}")
        
        for j in range(daily_reviews):
            # Pick a random review
            review_text = random.choice(SAMPLE_REVIEWS)
            
            try:
                # Analyze the review
                result = await analyzer.analyze_comprehensive(review_text)
                
                if 'error' not in result:
                    # Set the timestamp to the specific date
                    result['timestamp'] = date_offset.isoformat()
                    
                    # Save to database
                    review_id = await db.save_review(
                        result, 
                        ip_address="127.0.0.1", 
                        user_agent="Sample Data Generator"
                    )
                    
                    if review_id:
                        added_count += 1
                        print(f"  ✓ Added review {added_count}: {result['sentiment'].upper()} - {review_text[:50]}...")
                
            except Exception as e:
                print(f"  ❌ Error adding review: {e}")
                continue
    
    print(f"\n🎉 Successfully added {added_count} sample reviews!")
    print(f"📊 You should now see data in your sentiment distribution chart!")
    
    # Get some stats
    try:
        analytics = await db.get_analytics_summary()
        distribution = analytics.get('sentiment_distribution', {})
        
        print(f"\n📈 Current Statistics:")
        print(f"  • Total Reviews: {analytics.get('total_reviews', 0)}")
        print(f"  • Today's Reviews: {analytics.get('reviews_today', 0)}")
        print(f"  • Average Confidence: {analytics.get('average_confidence', 0):.1%}")
        
        if distribution.get('counts'):
            counts = distribution['counts']
            print(f"  • Positive: {counts.get('positive', 0)}")
            print(f"  • Negative: {counts.get('negative', 0)}")
            print(f"  • Neutral: {counts.get('neutral', 0)}")
            
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")

if __name__ == "__main__":
    asyncio.run(add_sample_data())
