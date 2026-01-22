from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    bot_token: str
    redis_url: str = "redis://localhost:6379"
    webhook_url: str | None = None
    admin_id: int = 0
    debug: bool = True

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
