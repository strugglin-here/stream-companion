"""Application configuration and settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict


# Application constants (not configurable)
APP_NAME = "Stream Companion"

# Package version: prefer the package-level ``app.__version__`` which is useful
# when the project is installed as a package (packaging tools read that
# attribute). Fall back to a literal if the import fails (e.g., during early
# bootstrap or when running from source without package metadata).
try:
    # Importing `app` here is safe because package import will execute
    # `app.__init__` first which only defines __version__.
    from app import __version__ as APP_VERSION  # type: ignore
except Exception:
    APP_VERSION = "0.1.0"


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    
    # Server (configurable)
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    # Directories to watch when running uvicorn with reload enabled
    # Useful during development to control which folders trigger reloads.
    reload_dirs: list[str] = ["app", "data"]
    
    # Database (configurable)
    database_url: str = "sqlite+aiosqlite:///./data/stream_companion.db"
    
    # Media (configurable)
    upload_directory: str = "./data/media"  # User-uploaded media files
    
    # CORS (configurable)
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
