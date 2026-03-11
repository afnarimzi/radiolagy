#!/usr/bin/env python3
"""
Simple API server startup without reload
"""
import uvicorn
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