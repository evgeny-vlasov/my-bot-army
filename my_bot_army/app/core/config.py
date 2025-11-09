from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Application
    APP_NAME: str = "My Bot Army"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str

    # Anthropic API
    ANTHROPIC_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
