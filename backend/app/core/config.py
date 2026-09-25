from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    secret_key: str = os.getenv("SAHI_SECRET_KEY", "change-this-in-production")
    database_url: str = os.getenv("SAHI_DATABASE_URL", "sqlite:///./sahi_scan.db")
    cors_origins: str = os.getenv("SAHI_CORS_ORIGINS", "http://localhost:5173")
    access_token_minutes: int = int(os.getenv("SAHI_ACCESS_TOKEN_MINUTES", str(60 * 24)))

settings = Settings()
