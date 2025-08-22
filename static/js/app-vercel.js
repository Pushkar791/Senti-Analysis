// Main application logic for Vercel deployment (HTTP only)
class SentimentApp {
    constructor() {
        this.currentAnalysis = null;
        this.recentReviews = [];
        this.isAnalyzing = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadInitialData();
        
        // Disable WebSocket features for Vercel
        this.disableWebSocketFeatures();
    }

    disableWebSocketFeatures() {
        // Hide real-time toggle since WebSocket is not available
        const realtimeToggle = document.getElementById('realtime-toggle');
        if (realtimeToggle) {
            realtimeToggle.checked = false;
            realtimeToggle.disabled = true;
            realtimeToggle.parentElement.style.opacity = '0.5';
            realtimeToggle.parentElement.title = 'Real-time features not available in Vercel deployment';
        }

        // Update connection status
        const connectionStatus = document.getElementById('connection-status');
        if (connectionStatus) {
            connectionStatus.classList.add('error');
            const span = connectionStatus.querySelector('span');
            if (span) {
                span.textContent = 'HTTP Mode';
            }
        }

        // Show notice about WebSocket limitation
        setTimeout(() => {
            this.showToast('HTTP Mode', 'Real-time features disabled. Using HTTP API only.', 'info');
        }, 2000);
    }

    initializeElements() {
        // Form elements
        this.form = document.getElementById('sentiment-form');
        this.textArea = document.getElementById('review-text');
        this.analyzeBtn = document.getElementById('analyze-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.sampleBtn = document.getElementById('sample-btn');
        this.realtimeToggle = document.getElementById('realtime-toggle');
        this.charCount = document.getElementById('char-count');

        // Results elements
        this.resultsSection = document.getElementById('results-section');
        this.sentimentIcon = document.getElementById('sentiment-icon');
        this.sentimentLabel = document.getElementById('sentiment-label');
        this.confidenceFill = document.getElementById('confidence-fill');
        this.confidenceText = document.getElementById('confidence-text');
        this.processingTime = document.getElementById('processing-time');
        this.wordCount = document.getElementById('word-count');
        this.sentenceCount = document.getElementById('sentence-count');

        // Model comparison elements
        this.vaderSentiment = document.getElementById('vader-sentiment');
        this.vaderConfidence = document.getElementById('vader-confidence');
        this.transformerSentiment = document.getElementById('transformer-sentiment');
        this.transformerConfidence = document.getElementById('transformer-confidence');

        // VADER score elements
        this.posScore = document.getElementById('pos-score');
        this.neuScore = document.getElementById('neu-score');
        this.negScore = document.getElementById('neg-score');
        this.compoundScore = document.getElementById('compound-score');
        
        // Recent reviews
        this.recentReviewsList = document.getElementById('recent-reviews-list');
        this.loadMoreBtn = document.getElementById('load-more-reviews');
    }

    bindEvents() {
        // Form submission
        this.form?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Text area events (no real-time for Vercel)
        this.textArea?.addEventListener('input', (e) => {
            this.updateCharCount();
        });

        // Button events
        this.clearBtn?.addEventListener('click', () => this.clearForm());
        this.sampleBtn?.addEventListener('click', () => this.loadSampleText());
        this.loadMoreBtn?.addEventListener('click', () => this.loadMoreReviews());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.handleSubmit();
            }
        });
    }

    async handleSubmit() {
        const text = this.textArea?.value?.trim();
        if (!text) {
            this.showToast('Empty Text', 'Please enter some text to analyze', 'warning');
            return;
        }

        await this.analyzeText(text);
    }

    async analyzeText(text) {
        if (this.isAnalyzing) return;
        
        this.isAnalyzing = true;
        this.setAnalyzeButtonState(true);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text, save_to_db: true })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            this.displayAnalysisResult(result);
            
            this.resultsSection.style.display = 'block';

        } catch (error) {
            console.error('Analysis error:', error);
            this.showToast('Analysis Error', error.message, 'error');
        } finally {
            this.isAnalyzing = false;
            this.setAnalyzeButtonState(false);
        }
    }

    displayAnalysisResult(result) {
        if (result.error) {
            this.showToast('Analysis Error', result.error, 'error');
            return;
        }

        this.currentAnalysis = result;

        // Update main sentiment display
        this.updateSentimentDisplay(result);
        
        // Update metrics
        this.updateMetrics(result);
        
        // Update model comparison
        this.updateModelComparison(result);
        
        // Update detailed analysis tabs
        this.updateDetailedAnalysis(result);
        
        // Update emotions chart
        if (result.emotions) {
            chartManager.createEmotionsChart(result.emotions);
        }

        // Show results section
        if (this.resultsSection) {
            this.resultsSection.style.display = 'block';
            this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    updateSentimentDisplay(result) {
        const { sentiment, confidence } = result;
        
        // Update icon
        if (this.sentimentIcon) {
            this.sentimentIcon.className = `sentiment-icon ${sentiment}`;
            this.sentimentIcon.innerHTML = this.getSentimentIcon(sentiment);
        }
        
        // Update label
        if (this.sentimentLabel) {
            this.sentimentLabel.textContent = sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
            this.sentimentLabel.className = sentiment;
        }
        
        // Update confidence bar
        if (this.confidenceFill) {
            setTimeout(() => {
                this.confidenceFill.style.width = `${confidence * 100}%`;
            }, 100);
        }
        
        if (this.confidenceText) {
            this.confidenceText.textContent = `Confidence: ${Math.round(confidence * 100)}%`;
        }
    }

    updateMetrics(result) {
        if (this.processingTime) {
            this.processingTime.textContent = `${result.processing_time || 0}s`;
        }
        
        const metrics = result.text_metrics || {};
        if (this.wordCount) {
            this.wordCount.textContent = metrics.word_count || 0;
        }
        
        if (this.sentenceCount) {
            this.sentenceCount.textContent = metrics.sentence_count || 0;
        }
    }

    updateModelComparison(result) {
        // VADER results
        if (result.vader_analysis) {
            const vader = result.vader_analysis;
            if (this.vaderSentiment) {
                this.vaderSentiment.textContent = vader.sentiment;
                this.vaderSentiment.className = `sentiment-badge ${vader.sentiment}`;
            }
            if (this.vaderConfidence) {
                this.vaderConfidence.textContent = `${Math.round(vader.confidence * 100)}% confidence`;
            }
        }

        // Transformer results (not available in Vercel)
        if (this.transformerSentiment) {
            this.transformerSentiment.textContent = 'N/A';
            this.transformerSentiment.className = 'sentiment-badge neutral';
        }
        if (this.transformerConfidence) {
            this.transformerConfidence.textContent = 'Not available in Vercel';
        }
    }

    updateDetailedAnalysis(result) {
        // Update VADER scores
        if (result.vader_analysis?.scores) {
            const scores = result.vader_analysis.scores;
            
            this.updateScoreBar('pos-score-fill', 'pos-score', scores.pos || 0);
            this.updateScoreBar('neu-score-fill', 'neu-score', scores.neu || 0);
            this.updateScoreBar('neg-score-fill', 'neg-score', scores.neg || 0);
            this.updateScoreBar('compound-score-fill', 'compound-score', Math.abs(scores.compound || 0));
        }

        // Update text metrics tab
        const textMetricsContent = document.getElementById('text-metrics-content');
        if (textMetricsContent && result.text_metrics) {
            textMetricsContent.innerHTML = this.generateTextMetricsHTML(result.text_metrics);
        }

        // Update raw data tab
        const rawDataContent = document.getElementById('raw-data-content');
        if (rawDataContent) {
            rawDataContent.textContent = JSON.stringify(result, null, 2);
        }
    }

    updateScoreBar(fillId, textId, value) {
        const fill = document.getElementById(fillId);
        const text = document.getElementById(textId);
        
        if (fill) {
            setTimeout(() => {
                fill.style.width = `${value * 100}%`;
            }, 100);
        }
        
        if (text) {
            text.textContent = value.toFixed(3);
        }
    }

    generateTextMetricsHTML(metrics) {
        return `
            <div class="metrics-grid">
                <div class="metric">
                    <strong>${metrics.word_count || 0}</strong>
                    <span>Words</span>
                </div>
                <div class="metric">
                    <strong>${metrics.sentence_count || 0}</strong>
                    <span>Sentences</span>
                </div>
                <div class="metric">
                    <strong>${(metrics.avg_word_length || 0).toFixed(1)}</strong>
                    <span>Avg Word Length</span>
                </div>
                <div class="metric">
                    <strong>${metrics.exclamation_count || 0}</strong>
                    <span>Exclamations</span>
                </div>
                <div class="metric">
                    <strong>${metrics.question_count || 0}</strong>
                    <span>Questions</span>
                </div>
                <div class="metric">
                    <strong>${Math.round((metrics.caps_ratio || 0) * 100)}%</strong>
                    <span>Uppercase Ratio</span>
                </div>
            </div>
        `;
    }

    getSentimentIcon(sentiment) {
        const icons = {
            positive: '😊',
            negative: '😟',
            neutral: '😐'
        };
        return icons[sentiment] || '🤔';
    }

    setAnalyzeButtonState(isLoading) {
        if (!this.analyzeBtn) return;
        
        if (isLoading) {
            this.analyzeBtn.disabled = true;
            this.analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        } else {
            this.analyzeBtn.disabled = false;
            this.analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze Sentiment';
        }
    }

    updateCharCount() {
        if (!this.textArea || !this.charCount) return;
        
        const length = this.textArea.value.length;
        this.charCount.textContent = length;
        
        // Change color based on length
        if (length > 8000) {
            this.charCount.style.color = '#ef4444';
        } else if (length > 6000) {
            this.charCount.style.color = '#f59e0b';
        } else {
            this.charCount.style.color = '#94a3b8';
        }
    }

    clearForm() {
        if (this.textArea) {
            this.textArea.value = '';
            this.updateCharCount();
        }
        
        if (this.resultsSection) {
            this.resultsSection.style.display = 'none';
        }
    }

    loadSampleText() {
        const samples = [
            "This product is absolutely amazing! I love how easy it is to use and the quality is outstanding. Highly recommended!",
            "I'm really disappointed with this purchase. The quality is poor and it doesn't work as advertised. Waste of money.",
            "The product is okay, nothing special. It does what it's supposed to do but there are better alternatives available.",
            "Exceptional service and fantastic product quality! The team went above and beyond to ensure customer satisfaction. Five stars!",
            "Terrible experience. The product arrived damaged and customer service was unhelpful. Will not buy again.",
            "Pretty good value for money. Some minor issues but overall satisfied with the purchase. Would consider buying again."
        ];
        
        const randomSample = samples[Math.floor(Math.random() * samples.length)];
        if (this.textArea) {
            this.textArea.value = randomSample;
            this.updateCharCount();
        }
    }

    async loadInitialData() {
        try {
            // Load recent reviews
            const response = await fetch('/api/recent-reviews?limit=20');
            const data = await response.json();
            
            if (data.reviews) {
                this.recentReviews = data.reviews;
                this.displayRecentReviews();
            }

            // Load analytics
            const analyticsResponse = await fetch('/api/analytics');
            const analyticsData = await analyticsResponse.json();
            
            if (analyticsData.summary) {
                updateAnalyticsSummary(analyticsData.summary);
            }
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    async loadMoreReviews() {
        try {
            const offset = this.recentReviews.length;
            const response = await fetch(`/api/recent-reviews?limit=20&offset=${offset}`);
            const data = await response.json();
            
            if (data.reviews && data.reviews.length > 0) {
                this.recentReviews.push(...data.reviews);
                this.displayRecentReviews();
            } else {
                this.showToast('No More Data', 'All reviews have been loaded', 'info');
                if (this.loadMoreBtn) {
                    this.loadMoreBtn.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error loading more reviews:', error);
            this.showToast('Error', 'Failed to load more reviews', 'error');
        }
    }

    displayRecentReviews() {
        if (!this.recentReviewsList) return;
        
        this.recentReviewsList.innerHTML = '';
        
        this.recentReviews.forEach(review => {
            const reviewElement = this.createReviewElement(review);
            this.recentReviewsList.appendChild(reviewElement);
        });
    }

    createReviewElement(review) {
        const div = document.createElement('div');
        div.className = 'review-item';
        
        const timeAgo = this.timeAgo(new Date(review.timestamp));
        const preview = review.text.length > 150 ? review.text.substring(0, 150) + '...' : review.text;
        
        div.innerHTML = `
            <div class="review-header">
                <span class="review-sentiment sentiment-badge ${review.sentiment}">
                    ${review.sentiment}
                </span>
                <span class="review-time">${timeAgo}</span>
            </div>
            <div class="review-text">${preview}</div>
        `;
        
        return div;
    }

    timeAgo(date) {
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }

    showToast(title, message, type = 'info') {
        showToast(title, message, type);
    }
}

// Global functions (same as before)
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const selectedContent = document.getElementById(tabId);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }
    
    event.target.classList.add('active');
}

function closeErrorModal() {
    const modal = document.getElementById('error-modal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

function showErrorModal(message) {
    const modal = document.getElementById('error-modal');
    const errorMessage = document.getElementById('error-message');
    
    if (modal && errorMessage) {
        errorMessage.textContent = message;
        modal.style.display = 'flex';
        modal.classList.add('show');
    }
}

function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="toast-icon ${iconMap[type]}"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Hide loading screen
    setTimeout(() => {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }
    }, 2000);
    
    // Initialize the main app
    window.sentimentApp = new SentimentApp();
    
    // Update model status
    setTimeout(() => {
        const modelStatus = document.getElementById('model-status');
        if (modelStatus) {
            const span = modelStatus.querySelector('span');
            if (span) {
                span.textContent = 'VADER Ready';
                modelStatus.classList.add('connected');
            }
        }
    }, 3000);
});
