from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    bot_token: str
    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql+asyncpg://bot:botpass@localhost:5432/botdb"
    admin_id: int = 0
    debug: bool = True

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
