// Chart management and visualization
class ChartManager {
    constructor() {
        this.charts = {};
        this.colors = {
            positive: '#22c55e',
            negative: '#ef4444',
            neutral: '#64748b',
            joy: '#fbbf24',
            anger: '#dc2626',
            sadness: '#3b82f6',
            fear: '#8b5cf6',
            surprise: '#f59e0b',
            disgust: '#059669'
        };
    }

    // Create sentiment distribution pie chart
    createSentimentPieChart(data) {
        const ctx = document.getElementById('sentiment-pie');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.sentimentPie) {
            this.charts.sentimentPie.destroy();
        }

        const sentiments = ['positive', 'negative', 'neutral'];
        const chartData = sentiments.map(sentiment => data.counts[sentiment] || 0);
        const backgroundColors = sentiments.map(sentiment => this.colors[sentiment]);

        this.charts.sentimentPie = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: sentiments.map(s => s.charAt(0).toUpperCase() + s.slice(1)),
                datasets: [{
                    data: chartData,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(color => color + '40'),
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000
                }
            }
        });
    }

    // Create emotions radar chart
    createEmotionsChart(emotions) {
        const ctx = document.getElementById('emotions-canvas');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.emotions) {
            this.charts.emotions.destroy();
        }

        const emotionLabels = Object.keys(emotions);
        const emotionValues = Object.values(emotions);
        const emotionColors = emotionLabels.map(emotion => this.colors[emotion] || '#64748b');

        this.charts.emotions = new Chart(ctx, {
            type: 'polarArea',
            data: {
                labels: emotionLabels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
                datasets: [{
                    data: emotionValues,
                    backgroundColor: emotionColors.map(color => color + '40'),
                    borderColor: emotionColors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${(context.raw * 100).toFixed(1)}%`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: Math.max(...emotionValues) * 1.2,
                        ticks: {
                            display: false
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                animation: {
                    duration: 1000
                }
            }
        });
    }

    // Create sentiment trends chart using Plotly
    createSentimentTrendsChart(trendsData) {
        const container = document.getElementById('sentiment-trends-chart');
        if (!container) return;

        // Prepare data for Plotly
        const dates = Object.keys(trendsData).sort();
        const sentiments = ['positive', 'negative', 'neutral'];
        
        const traces = sentiments.map(sentiment => {
            const counts = dates.map(date => {
                return trendsData[date] && trendsData[date][sentiment] 
                    ? trendsData[date][sentiment].count 
                    : 0;
            });

            return {
                x: dates,
                y: counts,
                type: 'scatter',
                mode: 'lines+markers',
                name: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
                line: {
                    color: this.colors[sentiment],
                    width: 3
                },
                marker: {
                    size: 8,
                    color: this.colors[sentiment],
                    symbol: 'circle'
                },
                fill: 'tonexty',
                fillcolor: this.colors[sentiment] + '20'
            };
        });

        const layout = {
            title: {
                text: 'Sentiment Trends Over Time',
                font: {
                    size: 16,
                    color: '#334155'
                }
            },
            xaxis: {
                title: 'Date',
                type: 'date',
                gridcolor: 'rgba(0,0,0,0.1)',
                tickfont: {
                    size: 12
                }
            },
            yaxis: {
                title: 'Number of Reviews',
                gridcolor: 'rgba(0,0,0,0.1)',
                tickfont: {
                    size: 12
                }
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: {
                l: 50,
                r: 30,
                t: 50,
                b: 50
            },
            legend: {
                x: 0,
                y: 1,
                bgcolor: 'rgba(255,255,255,0.8)',
                bordercolor: 'rgba(0,0,0,0.1)',
                borderwidth: 1
            },
            hovermode: 'x unified'
        };

        const config = {
            responsive: true,
            displayModeBar: false,
            showTips: false
        };

        Plotly.newPlot('sentiment-trends-chart', traces, layout, config);
    }

    // Update all charts with new data
    updateCharts(analyticsData) {
        try {
            // Update sentiment pie chart
            if (analyticsData.sentiment_distribution) {
                this.createSentimentPieChart(analyticsData.sentiment_distribution);
            }

            // Update emotions chart if available
            if (analyticsData.emotion_analysis && analyticsData.emotion_analysis.emotion_averages) {
                this.createEmotionsChart(analyticsData.emotion_analysis.emotion_averages);
            }

        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    // Update trends chart separately (requires different data)
    updateTrendsChart(trendsData) {
        try {
            if (trendsData && Object.keys(trendsData).length > 0) {
                this.createSentimentTrendsChart(trendsData);
            }
        } catch (error) {
            console.error('Error updating trends chart:', error);
        }
    }

    // Destroy all charts
    destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    // Create a mini emotion chart for individual analysis results
    createMiniEmotionChart(containerId, emotions) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Clear container
        container.innerHTML = '';

        // Create mini bars for each emotion
        const emotionEntries = Object.entries(emotions)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 6); // Show top 6 emotions

        emotionEntries.forEach(([emotion, value]) => {
            const emotionBar = document.createElement('div');
            emotionBar.className = 'mini-emotion-bar';
            
            const label = document.createElement('span');
            label.className = 'emotion-label';
            label.textContent = emotion.charAt(0).toUpperCase() + emotion.slice(1);
            
            const bar = document.createElement('div');
            bar.className = 'emotion-bar';
            
            const fill = document.createElement('div');
            fill.className = 'emotion-fill';
            fill.style.width = `${value * 100}%`;
            fill.style.backgroundColor = this.colors[emotion] || '#64748b';
            
            const valueSpan = document.createElement('span');
            valueSpan.className = 'emotion-value';
            valueSpan.textContent = `${(value * 100).toFixed(1)}%`;
            
            bar.appendChild(fill);
            emotionBar.appendChild(label);
            emotionBar.appendChild(bar);
            emotionBar.appendChild(valueSpan);
            
            container.appendChild(emotionBar);
        });
    }
}

// Global chart manager instance
const chartManager = new ChartManager();

// Helper function to update analytics summary
function updateAnalyticsSummary(data) {
    // Update stats
    const totalReviews = document.getElementById('total-reviews');
    const todayReviews = document.getElementById('today-reviews');
    const avgConfidence = document.getElementById('avg-confidence');
    const activeUsers = document.getElementById('active-users');

    if (totalReviews) totalReviews.textContent = data.total_reviews || 0;
    if (todayReviews) todayReviews.textContent = data.reviews_today || 0;
    if (avgConfidence) avgConfidence.textContent = `${Math.round((data.average_confidence || 0) * 100)}%`;
    if (activeUsers) {
        // This would typically come from WebSocket connection count
        activeUsers.textContent = (window.wsManager && window.wsManager.isConnected) ? '1+' : '0';
    }

    // Update charts
    chartManager.updateCharts(data);
}

// Helper function to load and update trends chart
async function loadTrendsChart() {
    try {
        const response = await fetch('/api/analytics?days=30');
        const data = await response.json();
        
        if (data.trends) {
            chartManager.updateTrendsChart(data.trends);
        }
    } catch (error) {
        console.error('Error loading trends data:', error);
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Load initial trends data
    setTimeout(loadTrendsChart, 1000);
    
    // Set up periodic updates for trends (every 5 minutes)
    setInterval(loadTrendsChart, 5 * 60 * 1000);
});

// Add some CSS for mini emotion chart
const style = document.createElement('style');
style.textContent = `
.mini-emotion-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
}

.emotion-label {
    min-width: 70px;
    font-weight: 500;
    color: var(--text-secondary);
}

.emotion-bar {
    flex: 1;
    height: 8px;
    background: var(--border-color);
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

.emotion-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.8s ease-out;
}

.emotion-value {
    min-width: 45px;
    text-align: right;
    font-size: 0.75rem;
    color: var(--text-muted);
}
`;
document.head.appendChild(style);

// Export chart manager globally
window.chartManager = chartManager;
