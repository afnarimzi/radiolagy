#!/usr/bin/env python3
"""
Simple API server startup without reload
"""
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify environment variables are loaded
required_keys = ['GROQ_API_KEY', 'GOOGLE_API_KEY', 'RISK_AGENT_API_KEY']
missing_keys = [key for key in required_keys if not os.getenv(key)]

if missing_keys:
    print(f"❌ Missing required environment variables: {', '.join(missing_keys)}")
    print("Please check your .env file and ensure all API keys are set.")
    exit(1)

from app.api.main import app

if __name__ == "__main__":
    print("🚀 Starting Radiology AI API Server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("Press Ctrl+C to stop the server")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")
    except Exception as e:
        print(f"❌ Server error: {e}")