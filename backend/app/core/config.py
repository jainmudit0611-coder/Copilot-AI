import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        extra="ignore"
    )

    APP_NAME: str = "CodePilot AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    SECRET_KEY: str = "supersecret-codepilot-jwt-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    FERNET_KEY: str = "gAAAAABlZ38S607_aY_Y9K5QJ4_R7Q0R1V4W4X5Y6Z7=" # Default Fernet key format

    # Database & Redis
    DATABASE_URL: str = "sqlite+aiosqlite:///./codepilot.db" # Default fallback for local dev/testing
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Configuration
    LLM_PROVIDER: str = "mock" # options: azure, openai, mock
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-small"
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"

    OPENAI_API_KEY: Optional[str] = None

    # GitHub Integration (Optional)
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: Optional[str] = None

    # Demo User Credentials (Development only)
    DEMO_USER_PASSWORD: str = "Password123!"

    # Limits & Thresholds
    MAX_REPOSITORY_SIZE_MB: int = 50
    MAX_FILE_SIZE_KB: int = 1024
    RATE_LIMIT_PER_MINUTE: int = 60

settings = Settings()
