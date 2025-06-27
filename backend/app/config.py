import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "FastAPI Chat"

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "chatapp")

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OAuth2 settings for Google
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
    )

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Gemini API Configuration
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


settings = Settings()
