# Real-time Sentiment Analysis System

A comprehensive, real-time sentiment analysis system that combines multiple NLP models to provide accurate sentiment detection for product reviews and text analysis.

## 🌟 Features

### Core Features
- **Real-time Analysis**: WebSocket-powered instant sentiment analysis
- **Multi-Model Approach**: Combines VADER and HuggingFace Transformer models
- **Comprehensive Analytics**: Detailed dashboards with trends and insights
- **Emotion Detection**: Advanced emotion indicators beyond basic sentiment
- **Responsive UI**: Modern, mobile-friendly interface with real-time updates

### Advanced Features
- **Model Comparison**: Side-by-side analysis from different models
- **Batch Processing**: Analyze multiple texts simultaneously
- **Data Persistence**: SQLite database for historical data
- **Performance Metrics**: Processing time and confidence scoring
- **Real-time Notifications**: Toast notifications for analysis updates
- **Interactive Charts**: Dynamic visualizations using Chart.js and Plotly

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Node.js (for development, optional)
- Modern web browser

## 📁 Project Structure

```
SEnt-Tracker/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── sentiment_analyzer.py # Advanced sentiment analysis models
│   └── database.py          # Database management and analytics
├── templates/
│   └── index.html           # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css        # Modern responsive styling
│   └── js/
│       ├── app.js           # Main application logic
│       ├── websocket.js     # WebSocket client management
│       └── charts.js        # Chart management and visualization
├── data/
│   └── sentiment_data.db    # SQLite database (auto-generated)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🛠️ Technical Architecture

### Backend (FastAPI + Python)
- **FastAPI**: High-performance async web framework
- **WebSocket Support**: Real-time bidirectional communication
- **Multiple NLP Models**:
  - VADER: Fast, rule-based sentiment analysis
  - HuggingFace Transformers: Advanced deep learning models
- **SQLite Database**: Lightweight, embedded database for data persistence
- **Async Processing**: Non-blocking analysis for better performance

### Frontend (HTML + CSS + JavaScript)
- **Modern UI**: Responsive design with CSS Grid and Flexbox
- **Real-time Updates**: WebSocket client for instant updates
- **Interactive Charts**: Chart.js for emotions, Plotly for trends
- **Progressive Enhancement**: Works with and without JavaScript

### Key Components

#### Sentiment Analyzer
- Combines multiple models for improved accuracy
- Preprocesses text (URL removal, HTML cleaning, etc.)
- Provides confidence scoring and detailed metrics
- Supports batch processing for multiple texts

#### Database Manager
- Stores analysis results with metadata
- Provides aggregated analytics and trends
- Supports date-range queries and filtering
- Maintains performance metrics

#### WebSocket Manager
- Handles real-time communication
- Automatic reconnection with exponential backoff
- Broadcasts updates to all connected clients
- Graceful degradation to HTTP fallback

## 📊 API Endpoints

### REST API
- `POST /api/analyze` - Analyze single text
- `POST /api/analyze-batch` - Analyze multiple texts
- `GET /api/analytics` - Get analytics summary
- `GET /api/recent-reviews` - Get recent analyses
- `GET /api/sentiment-distribution` - Get sentiment distribution
- `GET /api/emotion-analysis` - Get emotion analysis
- `GET /api/health` - Health check endpoint

### WebSocket
- `ws://localhost:8000/ws` - Real-time communication endpoint

## 🎯 Usage Examples

### Basic Sentiment Analysis
1. Enter text in the input field
2. Click "Analyze Sentiment" or enable real-time mode
3. View comprehensive results including:
   - Overall sentiment and confidence
   - Model comparison (VADER vs Transformer)
   - Emotion indicators
   - Text metrics and processing time

### Real-time Mode
1. Check "Real-time analysis" checkbox
2. Start typing in the text area
3. Analysis updates automatically as you type
4. Results appear instantly via WebSocket

### Batch Processing
Use the API endpoint to analyze multiple texts:
```bash
curl -X POST "http://localhost:8000/api/analyze-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "This product is amazing!",
      "Not satisfied with the quality.",
      "It works okay, nothing special."
    ]
  }'
```

## 📈 Analytics Dashboard

The system provides comprehensive analytics including:

- **Total Reviews**: Overall count of analyzed texts
- **Daily Statistics**: Reviews processed today
- **Average Confidence**: Mean confidence across all analyses
- **Sentiment Distribution**: Pie chart showing positive/negative/neutral ratios
- **Emotion Analysis**: Breakdown of detected emotions
- **Sentiment Trends**: Time-series visualization of sentiment patterns
- **Recent Activity**: Live feed of recent analyses

## 🔧 Configuration

### Environment Variables
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DB_PATH`: Database file path (default: data/sentiment_data.db)
- `LOG_LEVEL`: Logging level (default: INFO)

### Model Configuration
The system automatically downloads required models on first run:
- VADER: Built-in with `vaderSentiment` package
- HuggingFace: `cardiffnlp/twitter-roberta-base-sentiment-latest`

## 🚀 Performance Optimizations

### Backend Optimizations
- **Async Processing**: Non-blocking I/O operations
- **Model Caching**: Pre-loaded models for faster analysis
- **Database Connection Pooling**: Efficient database access
- **Background Tasks**: Non-blocking database writes

### Frontend Optimizations
- **Debounced Input**: Prevents excessive API calls during typing
- **Lazy Loading**: Charts load on demand
- **Efficient Updates**: Only update changed elements
- **Connection Management**: Automatic WebSocket reconnection

## 🔍 Model Accuracy and Performance

### VADER Sentiment Analyzer
- **Speed**: ~0.001-0.003 seconds per text
- **Best for**: Social media text, informal language
- **Accuracy**: Good for general sentiment, excellent for speed

### HuggingFace Transformer
- **Speed**: ~0.1-0.5 seconds per text (CPU) / ~0.01-0.05 seconds (GPU)
- **Best for**: Formal text, nuanced sentiment analysis
- **Accuracy**: State-of-the-art performance on most datasets

### Ensemble Approach
The system combines both models using a weighted approach:
- Agreement: Average confidence scores
- Disagreement: Favor transformer result with higher weight

## 🐛 Troubleshooting

### Common Issues

**Models not loading:**
```bash
# Clear cache and reinstall transformers
pip uninstall transformers
pip install transformers --no-cache-dir
```

**WebSocket connection issues:**
- Check firewall settings
- Ensure port 8000 is available
- Try HTTP fallback mode

**Database errors:**
- Ensure `data/` directory exists and is writable
- Check disk space availability

**Performance issues:**
- For GPU acceleration, install PyTorch with CUDA support
- Increase system memory for better model performance

## 📚 Dependencies

### Core Dependencies
- `fastapi`: Modern web framework
- `uvicorn`: ASGI server
- `websockets`: WebSocket support
- `vaderSentiment`: Rule-based sentiment analysis
- `transformers`: HuggingFace transformers
- `torch`: PyTorch for deep learning models

### Database & Analytics
- `aiosqlite`: Async SQLite support
- `pandas`: Data manipulation
- `numpy`: Numerical computing

### Visualization (Frontend)
- `Chart.js`: Interactive charts
- `Plotly.js`: Advanced data visualization
- `Font Awesome`: Icons and graphics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🎉 Key Improvements Over Previous Version

### Real-time Capabilities
- ✅ WebSocket integration for instant analysis
- ✅ Live updates across all connected clients
- ✅ Real-time typing analysis with debouncing

### Enhanced Analytics
- ✅ Comprehensive dashboard with multiple chart types
- ✅ Historical data storage and trends
- ✅ Emotion detection beyond basic sentiment

### Better User Experience
- ✅ Modern, responsive design
- ✅ Loading states and error handling
- ✅ Toast notifications for user feedback
- ✅ Keyboard shortcuts and accessibility

### Performance & Reliability
- ✅ Async processing throughout
- ✅ Automatic reconnection handling
- ✅ Graceful degradation when WebSocket unavailable
- ✅ Efficient database operations

### Developer Experience
- ✅ Clear project structure
- ✅ Comprehensive documentation
- ✅ Easy deployment and setup
- ✅ Extensible architecture

---

Built with ❤️ using FastAPI, WebSockets, and modern web technologies.
