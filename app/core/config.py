"""Application configuration and settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict


# Application constants (not configurable)
APP_NAME = "Stream Companion"
APP_VERSION = "0.1.0"


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    
    # Server (configurable)
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    
    # Database (configurable)
    database_url: str = "sqlite+aiosqlite:///./data/stream_companion.db"
    
    # Media (configurable)
    media_directory: str = "./media"
    
    # CORS (configurable)
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
