import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "FastAPI Social Auth"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OAuth2 settings for Google
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
    )


settings = Settings()
