import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram API credentials
    API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
    API_HASH = os.getenv("TELEGRAM_API_HASH", "")

    # Server config
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8001"))

    # Laravel integration
    LARAVEL_API_URL = os.getenv("LARAVEL_API_URL", "http://localhost:8000")
    LARAVEL_SECRET_KEY = os.getenv("LARAVEL_SECRET_KEY", "")

    # Session storage
    SESSION_PATH = os.getenv("SESSION_PATH", "./sessions")

config = Config()
