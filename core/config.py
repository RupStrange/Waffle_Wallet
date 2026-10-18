import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = "Waffle Wallet"
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:password@localhost:5432/waffle_wallet")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "5001"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
