from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    secret_key: str = os.getenv("SAHI_SECRET_KEY", "change-this-in-production")
    database_url: str = os.getenv("SAHI_DATABASE_URL", "sqlite:///./sahi_scan.db")
    cors_origins: str = os.getenv("SAHI_CORS_ORIGINS", "capacitor://localhost,http://localhost,https://localhost,http://192.168.0.141,http://192.168.0.120,http://localhost:5173")
    access_token_minutes: int = int(os.getenv("SAHI_ACCESS_TOKEN_MINUTES", str(60 * 24)))

settings = Settings()
