from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    bot_token: str
    redis_url: str = "redis://localhost:6379"
    database_url: str
    admin_id: int | None = None
    debug: bool = False
    
    # Admin panel
    admin_username: str = "admin"
    admin_password: str = "admin123"
    secret_key: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"

settings = Settings()
