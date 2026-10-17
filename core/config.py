import os
from functools import lru_cache


class Settings:
    app_name: str = "Waffle Wallet"
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./waffle_wallet.db")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "5001"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
