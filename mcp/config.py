"""
Configuration management for the MCP system.
"""

import os
import logging
from typing import Optional, Dict, Any
from pydantic import Field, PostgresDsn, RedisDsn, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_NAME: str = "ai-hivemind-mvp"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database settings
    DATABASE_URL: Optional[PostgresDsn] = None
    DATABASE_POOL_MIN: int = 1
    DATABASE_POOL_MAX: int = 10
    DATABASE_ECHO: bool = False
    
    # Redis settings
    REDIS_URL: Optional[RedisDsn] = None
    REDIS_POOL_MIN: int = 1
    REDIS_POOL_MAX: int = 10
    
    # Context settings
    CONTEXT_CACHE_TTL: int = 3600  # 1 hour
    CONTEXT_MAX_SIZE: int = 10000  # Max number of contexts to keep in memory
    
    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("DATABASE_URL", mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: Any) -> Any:
        """Assemble database URL from components if not provided directly."""
        if v is not None:
            return v
        
        # Try to build from components
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "hivemind")
        
        if db_user and db_host and db_name:
            return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        raise ValueError("Database URL not configured")
    
    @field_validator("REDIS_URL", mode='before')
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: Any) -> Any:
        """Assemble Redis URL from components if not provided directly."""
        if v is not None:
            return v
        
        # Try to build from components
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_db = os.getenv("REDIS_DB", "0")
        redis_password = os.getenv("REDIS_PASSWORD")
        
        auth_part = f":{redis_password}@" if redis_password else ""
        return f"redis://{auth_part}{redis_host}:{redis_port}/{redis_db}"


@lru_cache()
def get_settings() -> Settings:
    """Get application settings with caching."""
    return Settings()


def configure_logging() -> None:
    """Configure application logging."""
    settings = get_settings()
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )
    
    # Set log levels for libraries
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    logger.info(f"Logging configured with level {settings.LOG_LEVEL}")
