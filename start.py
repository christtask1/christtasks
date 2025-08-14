#!/usr/bin/env python3
"""
Production startup script for Render deployment
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 10000))
    
    print("Starting Christian Apologetics RAG Chatbot in production mode...")
    print(f"Server will run on port: {port}")
    
    # Check if required environment variables are set
    required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("Make sure to set these in your Render service environment variables")
    
    # Run the app in production mode
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # No reload in production
        log_level="info",
        access_log=True
    )

