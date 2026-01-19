#!/usr/bin/env python3
"""
Run the Telegram Bot Creator Service
"""
import uvicorn
from app.config import config

if __name__ == "__main__":
    print(f"Starting Telegram Bot Creator Service on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )
