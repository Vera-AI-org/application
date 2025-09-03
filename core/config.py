import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

APP_ENV = os.getenv("APP_ENV", "develop")

env_file_path = f".env.{APP_ENV}" if APP_ENV != "develop" else ".env"

class Settings(BaseSettings):
    APP_ENV: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_PORT: int
    DATABASE_URL: str
    DB_HOST: Optional[str] = None
    API_PORT: int
    FIREBASE_SERVICE_ACCOUNT_KEY_PATH: Path
    GOOGLE_API_KEY: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=env_file_path, 
        env_file_encoding='utf-8', 
        extra='ignore'
    )

settings = Settings()