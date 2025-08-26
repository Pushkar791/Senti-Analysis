import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from collections import Counter, defaultdict
import statistics

class SuggestionEngine:
    """
    Advanced suggestion engine that analyzes sentiment patterns and generates
    actionable recommendations for product owners to improve their products.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Define suggestion categories and their triggers
        self.suggestion_categories = {
            'customer_satisfaction': {
                'priority': 'high',
                'description': 'Suggestions to improve overall customer satisfaction'
            },
            'product_quality': {
                'priority': 'high', 
                'description': 'Recommendations for product quality improvements'
            },
            'user_experience': {
                'priority': 'medium',
                'description': 'UX/UI and usability enhancement suggestions'
            },
            'customer_service': {
                'priority': 'medium',
                'description': 'Customer support and service improvement ideas'
            },
            'pricing_value': {
                'priority': 'medium',
                'description': 'Pricing strategy and value proposition suggestions'
            },
            'feature_requests': {
                'priority': 'low',
                'description': 'New feature ideas based on customer feedback'
            },
            'marketing_messaging': {
                'priority': 'low',
                'description': 'Marketing and communication improvement suggestions'
            }
        }
        
        # Keywords associated with different issues
        self.issue_keywords = {
            'quality_issues': [
                'broken', 'defective', 'poor quality', 'cheap', 'flimsy', 
                'doesn\'t work', 'malfunctioned', 'defect', 'faulty',
                'low quality', 'terrible quality'
            ],
            'usability_issues': [
                'confusing', 'hard to use', 'difficult', 'complicated',
                'unclear', 'not intuitive', 'confusing interface',
                'hard to navigate', 'user-unfriendly'
            ],
            'performance_issues': [
                'slow', 'laggy', 'crashes', 'freezes', 'unresponsive',
                'loading', 'timeout', 'performance', 'speed'
            ],
            'customer_service_issues': [
                'rude staff', 'poor service', 'unhelpful', 'long wait',
                'no response', 'bad support', 'customer service',
                'support team', 'representatives'
            ],
            'pricing_issues': [
                'expensive', 'overpriced', 'too costly', 'not worth',
                'money', 'price', 'cost', 'cheap alternative',
                'value for money', 'overcharged'
            ],
            'delivery_issues': [
                'late delivery', 'shipping', 'delayed', 'not arrived',
                'delivery problem', 'shipping cost', 'packaging'
            ]
        }
    
    async def analyze_sentiment_patterns(self, days: int = 30) -> Dict:
        """Analyze sentiment patterns over time to identify trends"""
        if not self.db:
            return {}
            
        try:
            # Get sentiment trends
            trends = await self.db.get_sentiment_trends(days)
            distribution = await self.db.get_sentiment_distribution(days)
            emotion_analysis = await self.db.get_emotion_analysis(days)
            recent_reviews = await self.db.get_recent_reviews(limit=200)
            
            analysis = {
                'sentiment_trend': self._analyze_sentiment_trend(trends),
                'sentiment_distribution': distribution,
                'emotion_patterns': emotion_analysis,
                'common_issues': await self._identify_common_issues(recent_reviews),
                'satisfaction_score': self._calculate_satisfaction_score(distribution),
                'review_volume_trend': self._analyze_review_volume(trends),
                'time_period': days
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment patterns: {e}")
            return {}
    
    def _analyze_sentiment_trend(self, trends: Dict) -> Dict:
        """Analyze if sentiment is improving, declining, or stable"""
        if not trends:
            return {'trend': 'insufficient_data', 'confidence': 0}
        
        # Convert trends to time series
        dates = sorted(trends.keys())
        if len(dates) < 3:
            return {'trend': 'insufficient_data', 'confidence': 0.3}
        
        # Calculate weighted sentiment scores over time
        sentiment_scores = []
        for date in dates:
            day_data = trends[date]
            pos = day_data.get('positive', {}).get('count', 0)
            neu = day_data.get('neutral', {}).get('count', 0) 
            neg = day_data.get('negative', {}).get('count', 0)
            
            total = pos + neu + neg
            if total > 0:
                # Weight: positive=1, neutral=0, negative=-1
                score = (pos - neg) / total
                sentiment_scores.append(score)
        
        if len(sentiment_scores) < 2:
            return {'trend': 'insufficient_data', 'confidence': 0.3}
        
        # Calculate trend using simple linear regression slope
        recent_scores = sentiment_scores[-7:] if len(sentiment_scores) >= 7 else sentiment_scores
        
        if len(recent_scores) >= 2:
            x_vals = list(range(len(recent_scores)))
            slope = self._calculate_slope(x_vals, recent_scores)
            
            if slope > 0.02:
                trend = 'improving'
            elif slope < -0.02:
                trend = 'declining'
            else:
                trend = 'stable'
                
            confidence = min(0.9, len(recent_scores) / 10 + abs(slope))
        else:
            trend = 'stable'
            confidence = 0.3
            
        return {
            'trend': trend,
            'confidence': round(confidence, 2),
            'slope': round(slope if 'slope' in locals() else 0, 4),
            'recent_average': round(statistics.mean(recent_scores), 3) if recent_scores else 0
        }
    
    def _calculate_slope(self, x_vals: List, y_vals: List) -> float:
        """Calculate slope for trend analysis"""
        if len(x_vals) != len(y_vals) or len(x_vals) < 2:
            return 0
            
        n = len(x_vals)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_x_sq = sum(x * x for x in x_vals)
        
        denominator = n * sum_x_sq - sum_x * sum_x
        if denominator == 0:
            return 0
            
        return (n * sum_xy - sum_x * sum_y) / denominator
    
    async def _identify_common_issues(self, reviews: List[Dict]) -> Dict:
        """Identify common issues mentioned in negative reviews"""
        issue_counts = defaultdict(int)
        total_negative = 0
        
        for review in reviews:
            if review.get('sentiment') == 'negative':
                total_negative += 1
                text = review.get('text', '').lower()
                
                for issue_type, keywords in self.issue_keywords.items():
                    for keyword in keywords:
                        if keyword in text:
                            issue_counts[issue_type] += 1
                            break  # Count once per review per issue type
        
        # Calculate percentages and sort by frequency
        issue_percentages = {}
        for issue, count in issue_counts.items():
            if total_negative > 0:
                percentage = (count / total_negative) * 100
                if percentage >= 5:  # Only include issues mentioned in 5%+ of negative reviews
                    issue_percentages[issue] = {
                        'count': count,
                        'percentage': round(percentage, 1),
                        'severity': 'high' if percentage >= 20 else 'medium' if percentage >= 10 else 'low'
                    }
        
        return dict(sorted(issue_percentages.items(), key=lambda x: x[1]['percentage'], reverse=True))
    
    def _calculate_satisfaction_score(self, distribution: Dict) -> Dict:
        """Calculate overall satisfaction score (0-100)"""
        counts = distribution.get('counts', {})
        total = distribution.get('total', 0)
        
        if total == 0:
            return {'score': 0, 'grade': 'F', 'message': 'No data available'}
        
        pos = counts.get('positive', 0)
        neu = counts.get('neutral', 0) 
        neg = counts.get('negative', 0)
        
        # Weight: positive=100, neutral=50, negative=0
        weighted_score = (pos * 100 + neu * 50 + neg * 0) / total
        
        # Determine grade
        if weighted_score >= 80:
            grade = 'A'
        elif weighted_score >= 70:
            grade = 'B'
        elif weighted_score >= 60:
            grade = 'C'
        elif weighted_score >= 50:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': round(weighted_score, 1),
            'grade': grade,
            'total_reviews': total,
            'positive_ratio': round((pos / total) * 100, 1) if total > 0 else 0,
            'negative_ratio': round((neg / total) * 100, 1) if total > 0 else 0
        }
    
    def _analyze_review_volume(self, trends: Dict) -> Dict:
        """Analyze if review volume is increasing or decreasing"""
        if not trends:
            return {'trend': 'no_data', 'change': 0}
        
        dates = sorted(trends.keys())
        if len(dates) < 7:
            return {'trend': 'insufficient_data', 'change': 0}
        
        # Calculate daily totals
        daily_totals = []
        for date in dates:
            day_data = trends[date]
            daily_total = sum(
                sentiment_data.get('count', 0) 
                for sentiment_data in day_data.values()
                if isinstance(sentiment_data, dict)
            )
            daily_totals.append(daily_total)
        
        if len(daily_totals) < 7:
            return {'trend': 'insufficient_data', 'change': 0}
        
        # Compare recent period vs previous period
        recent_avg = statistics.mean(daily_totals[-7:])
        previous_avg = statistics.mean(daily_totals[-14:-7]) if len(daily_totals) >= 14 else statistics.mean(daily_totals[:-7])
        
        if previous_avg == 0:
            change = 0
        else:
            change = ((recent_avg - previous_avg) / previous_avg) * 100
        
        if change > 10:
            trend = 'increasing'
        elif change < -10:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change': round(change, 1),
            'recent_avg': round(recent_avg, 1),
            'previous_avg': round(previous_avg, 1)
        }
    
    async def generate_suggestions(self, analysis: Dict = None, days: int = 30) -> List[Dict]:
        """Generate actionable suggestions based on sentiment analysis"""
        if not analysis:
            analysis = await self.analyze_sentiment_patterns(days)
        
        suggestions = []
        
        # Generate suggestions based on satisfaction score
        satisfaction = analysis.get('satisfaction_score', {})
        suggestions.extend(self._generate_satisfaction_suggestions(satisfaction))
        
        # Generate suggestions based on sentiment trends
        trend_data = analysis.get('sentiment_trend', {})
        suggestions.extend(self._generate_trend_suggestions(trend_data))
        
        # Generate suggestions based on common issues
        issues = analysis.get('common_issues', {})
        suggestions.extend(self._generate_issue_suggestions(issues))
        
        # Generate suggestions based on emotions
        emotions = analysis.get('emotion_patterns', {})
        suggestions.extend(self._generate_emotion_suggestions(emotions))
        
        # Generate suggestions based on review volume
        volume = analysis.get('review_volume_trend', {})
        suggestions.extend(self._generate_volume_suggestions(volume))
        
        # Add metadata to suggestions
        for suggestion in suggestions:
            suggestion.update({
                'generated_at': datetime.now().isoformat(),
                'analysis_period': days,
                'id': f"sug_{hash(suggestion['title'] + suggestion['category'])}_{int(datetime.now().timestamp())}"
            })
        
        # Sort by priority and impact
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        suggestions.sort(
            key=lambda x: (priority_order.get(x['priority'], 0), x.get('impact_score', 0)), 
            reverse=True
        )
        
        return suggestions[:20]  # Return top 20 suggestions
    
    def _generate_satisfaction_suggestions(self, satisfaction: Dict) -> List[Dict]:
        """Generate suggestions based on satisfaction score"""
        suggestions = []
        score = satisfaction.get('score', 0)
        negative_ratio = satisfaction.get('negative_ratio', 0)
        
        if score < 50:
            suggestions.append({
                'title': 'Critical: Implement comprehensive quality improvement program',
                'description': f'Your satisfaction score is {score}/100, indicating serious customer satisfaction issues. Consider conducting a thorough review of your product/service quality.',
                'category': 'customer_satisfaction',
                'priority': 'high',
                'impact_score': 90,
                'effort_estimate': 'high',
                'expected_outcome': 'Significant improvement in customer satisfaction and retention',
                'action_items': [
                    'Conduct customer interviews to identify root causes',
                    'Review and improve product quality processes',
                    'Implement customer feedback loop',
                    'Train customer-facing staff on service excellence'
                ]
            })
            
        elif score < 70:
            suggestions.append({
                'title': 'Enhance customer experience to boost satisfaction',
                'description': f'Your satisfaction score is {score}/100. There\'s room for improvement to reach excellent customer satisfaction levels.',
                'category': 'customer_satisfaction', 
                'priority': 'medium',
                'impact_score': 70,
                'effort_estimate': 'medium',
                'expected_outcome': 'Improved customer loyalty and positive word-of-mouth',
                'action_items': [
                    'Analyze customer journey for pain points',
                    'Implement proactive customer support',
                    'Gather and act on customer feedback regularly',
                    'Optimize product/service based on user needs'
                ]
            })
        
        if negative_ratio > 30:
            suggestions.append({
                'title': 'Address high negative feedback rate',
                'description': f'{negative_ratio}% of your reviews are negative. Focus on converting detractors into promoters.',
                'category': 'customer_satisfaction',
                'priority': 'high',
                'impact_score': 80,
                'effort_estimate': 'medium',
                'expected_outcome': 'Reduced negative feedback and improved brand reputation',
                'action_items': [
                    'Create rapid response system for negative feedback',
                    'Implement service recovery protocols',
                    'Follow up with dissatisfied customers',
                    'Use negative feedback to improve products/services'
                ]
            })
        
        return suggestions
    
    def _generate_trend_suggestions(self, trend_data: Dict) -> List[Dict]:
        """Generate suggestions based on sentiment trends"""
        suggestions = []
        trend = trend_data.get('trend', 'stable')
        confidence = trend_data.get('confidence', 0)
        
        if trend == 'declining' and confidence > 0.5:
            suggestions.append({
                'title': 'Urgent: Address declining customer sentiment',
                'description': 'Customer sentiment has been declining. Take immediate action to identify and resolve issues causing dissatisfaction.',
                'category': 'customer_satisfaction',
                'priority': 'high', 
                'impact_score': 95,
                'effort_estimate': 'high',
                'expected_outcome': 'Halt negative trend and restore customer confidence',
                'action_items': [
                    'Conduct emergency customer satisfaction survey',
                    'Analyze recent changes that might have caused decline',
                    'Implement immediate fixes for critical issues',
                    'Communicate transparently with customers about improvements'
                ]
            })
            
        elif trend == 'improving' and confidence > 0.6:
            suggestions.append({
                'title': 'Capitalize on positive sentiment momentum', 
                'description': 'Customer sentiment is improving! Now is the perfect time to strengthen your position and build on this positive trend.',
                'category': 'marketing_messaging',
                'priority': 'medium',
                'impact_score': 60,
                'effort_estimate': 'low',
                'expected_outcome': 'Accelerated growth and stronger market position',
                'action_items': [
                    'Showcase positive customer testimonials',
                    'Launch customer referral program',
                    'Increase marketing spend to capitalize on momentum', 
                    'Gather and share success stories'
                ]
            })
        
        return suggestions
    
    def _generate_issue_suggestions(self, issues: Dict) -> List[Dict]:
        """Generate suggestions based on common issues"""
        suggestions = []
        
        for issue_type, data in issues.items():
            if data['severity'] in ['high', 'medium']:
                suggestion = self._get_issue_specific_suggestion(issue_type, data)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _get_issue_specific_suggestion(self, issue_type: str, data: Dict) -> Dict:
        """Get specific suggestions for different issue types"""
        percentage = data['percentage']
        severity = data['severity']
        
        issue_suggestions = {
            'quality_issues': {
                'title': f'Address product quality concerns ({percentage}% of negative reviews)',
                'description': f'Quality issues are mentioned in {percentage}% of negative reviews. Focus on improving product quality and reliability.',
                'category': 'product_quality',
                'action_items': [
                    'Implement stricter quality control processes',
                    'Review supplier/manufacturer standards',
                    'Conduct product testing and durability analysis',
                    'Create quality assurance checklist'
                ]
            },
            'usability_issues': {
                'title': f'Improve product usability and user experience ({percentage}% mention)',
                'description': f'Users find your product difficult to use. {percentage}% of negative reviews mention usability problems.',
                'category': 'user_experience',
                'action_items': [
                    'Conduct usability testing with real users',
                    'Simplify user interface and workflows',
                    'Create better onboarding and tutorials',
                    'Implement user-centered design principles'
                ]
            },
            'performance_issues': {
                'title': f'Optimize performance and reliability ({percentage}% mention)',
                'description': f'Performance issues are affecting customer satisfaction. {percentage}% of negative reviews cite performance problems.',
                'category': 'product_quality',
                'action_items': [
                    'Conduct performance auditing and optimization',
                    'Upgrade infrastructure and systems',
                    'Implement monitoring and alerting',
                    'Optimize code and resource usage'
                ]
            },
            'customer_service_issues': {
                'title': f'Enhance customer service quality ({percentage}% mention)',
                'description': f'Customer service issues are mentioned in {percentage}% of negative reviews. Improve support quality and responsiveness.',
                'category': 'customer_service',
                'action_items': [
                    'Train customer service representatives',
                    'Implement faster response time goals',
                    'Create comprehensive FAQ and self-service options',
                    'Monitor and improve service quality metrics'
                ]
            },
            'pricing_issues': {
                'title': f'Review pricing strategy and value proposition ({percentage}% mention)',
                'description': f'Pricing concerns appear in {percentage}% of negative reviews. Consider adjusting pricing or improving perceived value.',
                'category': 'pricing_value',
                'action_items': [
                    'Conduct competitive pricing analysis',
                    'Survey customers on price sensitivity',
                    'Improve value communication and benefits',
                    'Consider tiered pricing or promotions'
                ]
            },
            'delivery_issues': {
                'title': f'Improve delivery and logistics ({percentage}% mention)',
                'description': f'Delivery issues are mentioned in {percentage}% of negative reviews. Focus on improving shipping and fulfillment.',
                'category': 'user_experience',
                'action_items': [
                    'Review shipping partners and processes',
                    'Implement order tracking and communication',
                    'Optimize packaging to prevent damage',
                    'Set realistic delivery expectations'
                ]
            }
        }
        
        if issue_type in issue_suggestions:
            suggestion = issue_suggestions[issue_type].copy()
            suggestion.update({
                'priority': 'high' if severity == 'high' else 'medium',
                'impact_score': min(90, 20 + percentage * 2),
                'effort_estimate': 'high' if severity == 'high' else 'medium',
                'expected_outcome': f'Reduce {issue_type.replace("_", " ")} complaints by addressing root causes'
            })
            return suggestion
        
        return None
    
    def _generate_emotion_suggestions(self, emotions: Dict) -> List[Dict]:
        """Generate suggestions based on emotional patterns"""
        suggestions = []
        emotion_averages = emotions.get('emotion_averages', {})
        
        if not emotion_averages:
            return suggestions
        
        # High anger suggests serious issues
        if emotion_averages.get('anger', 0) > 0.15:
            suggestions.append({
                'title': 'Address customer frustration and anger',
                'description': f'High anger levels detected in customer feedback. Customers are frustrated - this needs immediate attention.',
                'category': 'customer_satisfaction',
                'priority': 'high',
                'impact_score': 85,
                'effort_estimate': 'medium',
                'expected_outcome': 'Reduced customer frustration and improved satisfaction',
                'action_items': [
                    'Identify specific causes of customer anger',
                    'Implement conflict resolution training',
                    'Create empathy-driven customer service protocols',
                    'Follow up with angry customers to resolve issues'
                ]
            })
        
        # Low joy suggests missed opportunities
        if emotion_averages.get('joy', 0) < 0.1:
            suggestions.append({
                'title': 'Increase customer delight and positive experiences',
                'description': 'Low joy levels in customer feedback suggest missed opportunities to create delightful experiences.',
                'category': 'user_experience',
                'priority': 'medium',
                'impact_score': 65,
                'effort_estimate': 'medium',
                'expected_outcome': 'Increased customer delight and positive word-of-mouth',
                'action_items': [
                    'Add surprise and delight elements to customer journey',
                    'Celebrate customer milestones and achievements',
                    'Implement gamification or reward programs',
                    'Focus on exceeding customer expectations'
                ]
            })
        
        return suggestions
    
    def _generate_volume_suggestions(self, volume: Dict) -> List[Dict]:
        """Generate suggestions based on review volume trends"""
        suggestions = []
        trend = volume.get('trend', 'stable')
        change = volume.get('change', 0)
        
        if trend == 'decreasing' and change < -20:
            suggestions.append({
                'title': 'Increase customer engagement and feedback collection',
                'description': f'Review volume has decreased by {abs(change)}%. This might indicate reduced customer engagement or satisfaction.',
                'category': 'marketing_messaging',
                'priority': 'medium',
                'impact_score': 50,
                'effort_estimate': 'low',
                'expected_outcome': 'Increased customer engagement and valuable feedback',
                'action_items': [
                    'Implement proactive review request system',
                    'Incentivize customer feedback with rewards',
                    'Follow up with customers after purchase/interaction',
                    'Make leaving reviews easier and more accessible'
                ]
            })
        
        return suggestions
