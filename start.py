#!/usr/bin/env python3
"""
Startup script for Railway deployment
Handles NLTK data downloads and starts the FastAPI application
"""
import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_nltk_data():
    """Download required NLTK data"""
    try:
        import nltk
        logger.info("Downloading NLTK data...")
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        logger.info("NLTK data downloaded successfully")
    except Exception as e:
        logger.warning(f"NLTK data download failed: {e}")

def main():
    """Main startup function"""
    logger.info("Starting SEnt-Tracker application...")
    
    # Download NLTK data
    download_nltk_data()
    
    # Get port from environment
    port = os.getenv('PORT', '8000')
    
    # Start the FastAPI application
    logger.info(f"Starting uvicorn server on port {port}")
    
    # Use subprocess to start uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "backend.main:app", 
        "--host", "0.0.0.0", 
        "--port", port
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
