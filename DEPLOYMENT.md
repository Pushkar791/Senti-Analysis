# Deployment Guide for Vercel

This guide will help you deploy your Sentiment Analysis System to Vercel.

## 🚀 Quick Deployment Steps

### 1. Prepare Your Code

First, make sure you have the Vercel-optimized files:

1. **Update the HTML template** to use the Vercel-compatible JavaScript:
   ```html
   <!-- Replace the script tags in templates/index.html -->
   <script src="/static/js/charts.js"></script>
   <script src="/static/js/app-vercel.js"></script>
   ```

2. **Use the lightweight requirements**:
   Rename `requirements-vercel.txt` to `requirements.txt`:
   ```bash
   cp requirements-vercel.txt requirements.txt
   ```

3. **Update the sentiment analyzer import** in `api/index.py`:
   Replace the import to use the Vercel-compatible version:
   ```python
   from sentiment_analyzer_vercel import AdvancedSentimentAnalyzer
   ```

### 2. Deploy to Vercel

#### Option A: Deploy via Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from your project directory**:
   ```bash
   vercel
   ```

4. **Follow the prompts**:
   - Set up and deploy: Yes
   - Which scope: Choose your account
   - Link to existing project: No
   - Project name: sentiment-analysis (or your preferred name)
   - Directory: . (current directory)

#### Option B: Deploy via GitHub Integration

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Vercel deployment"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will automatically detect the configuration

### 3. Configure Environment Variables (Optional)

If you need environment variables, add them in the Vercel dashboard:

- Go to your project dashboard
- Navigate to "Settings" > "Environment Variables"
- Add any required variables

## 📁 Project Structure for Vercel

```
SEnt-Tracker/
├── api/
│   └── index.py          # Main FastAPI app (Vercel entry point)
├── backend/
│   ├── sentiment_analyzer_vercel.py  # VADER-only analyzer
│   └── database.py       # Database management
├── static/
│   ├── css/style.css
│   └── js/
│       ├── app-vercel.js # HTTP-only frontend
│       └── charts.js
├── templates/
│   └── index.html
├── vercel.json           # Vercel configuration
├── requirements.txt      # Lightweight dependencies
└── README.md
```

## 🔧 Key Changes for Vercel

### Backend Changes

1. **Serverless Architecture**: Uses `api/index.py` as the main entry point
2. **No WebSocket Support**: WebSockets aren't supported in Vercel's serverless functions
3. **Lightweight Dependencies**: Removed heavy ML libraries (transformers, torch)
4. **VADER Only**: Uses only VADER sentiment analyzer to stay within size limits
5. **Temporary Database**: Uses `/tmp` directory for SQLite (data won't persist)

### Frontend Changes

1. **HTTP-Only Communication**: Removed WebSocket client
2. **Disabled Real-time Features**: Real-time toggle is disabled
3. **Fallback UI**: Shows appropriate messages about limitations

## ⚡ Performance Considerations

### Vercel Limitations

- **Function Size**: Max 50MB (uncompressed)
- **Execution Time**: Max 60 seconds for Hobby plan
- **Memory**: 1GB RAM limit
- **No Persistent Storage**: Database resets on each deployment

### Optimizations Applied

- **Removed Heavy Dependencies**: No PyTorch or Transformers
- **VADER Only**: Fast, lightweight sentiment analysis
- **Simplified Database**: Basic SQLite with graceful fallbacks
- **Error Handling**: Graceful degradation when services fail

## 🌐 After Deployment

### Testing Your Deployment

1. **Check Health Endpoint**:
   ```bash
   curl https://your-app.vercel.app/api/health
   ```

2. **Test Sentiment Analysis**:
   ```bash
   curl -X POST "https://your-app.vercel.app/api/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "This is amazing!"}'
   ```

3. **Visit the Web Interface**:
   Open `https://your-app.vercel.app` in your browser

### Expected Behavior

✅ **Working Features**:
- Sentiment analysis using VADER
- HTTP API endpoints
- Basic analytics (limited due to temporary storage)
- Responsive web interface
- Emotion detection
- Text metrics

❌ **Limitations**:
- No real-time WebSocket updates
- No transformer model (HuggingFace)
- No persistent data storage
- No real-time typing analysis

## 🔄 Updates and Redeployments

### Automatic Deployments (GitHub Integration)

If you connected via GitHub, Vercel will automatically redeploy when you push to your main branch.

### Manual Deployments (CLI)

```bash
vercel --prod
```

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors**:
- Make sure you're using `sentiment_analyzer_vercel.py`
- Check that all imports are available in the lightweight requirements

**2. Function Timeout**:
- Sentiment analysis should be fast with VADER
- If timeouts occur, check for infinite loops or heavy processing

**3. Module Not Found**:
- Ensure all files are in the correct directories
- Check that paths in `api/index.py` are correct

**4. Database Issues**:
- Remember that database is temporary
- Check that `/tmp` directory is being used

### Debugging Tips

1. **Check Vercel Logs**:
   ```bash
   vercel logs
   ```

2. **Local Testing**:
   ```bash
   vercel dev
   ```

3. **Function Logs**: Check the Vercel dashboard for detailed error logs

## 💰 Costs

### Vercel Pricing

- **Hobby Plan**: Free
  - 100GB bandwidth per month
  - 100 GB-hours of compute time
  - Automatic HTTPS
  - No custom domains limit

- **Pro Plan**: $20/month per member
  - More bandwidth and compute time
  - Advanced analytics
  - Team collaboration features

For a sentiment analysis tool, the Hobby plan should be sufficient for moderate usage.

## 🚀 Alternative Deployment Options

If you need the full feature set (WebSockets, Transformers), consider:

1. **Heroku**: Supports WebSockets and long-running processes
2. **Railway**: Good for Python apps with ML dependencies
3. **DigitalOcean App Platform**: Supports WebSockets
4. **Self-hosted VPS**: Full control and features

## 📞 Support

If you encounter issues:

1. Check the [Vercel documentation](https://vercel.com/docs)
2. Review the deployment logs in your Vercel dashboard
3. Test locally with `vercel dev` first
4. Check that all dependencies are in `requirements.txt`

---

**Note**: This Vercel deployment is optimized for quick deployment and demonstration. For production use with full features, consider a platform that supports WebSockets and persistent storage.
