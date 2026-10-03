"""
PocketSmart AI Runner Script
"""
import sys
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"🚀 Starting {settings.APP_NAME} on http://{settings.HOST}:{settings.PORT}")
    print("💡 Tip: Set GEMINI_API_KEY in your .env file to enable live Google Gemini 1.5 Flash features.")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
