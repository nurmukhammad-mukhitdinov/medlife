import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=True)


class DatabaseConfig(BaseModel):
    dsn: str = "postgresql://user:password@host:port/dbname"
    async_dsn: str = "postgresql+asyncpg://user:password@host:port/dbname"


class Config(BaseSettings):
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "MedLife Healthcare API"
    ENVIRONMENT: str = "development"
    TRUSTED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["*"]
    database: DatabaseConfig = DatabaseConfig()
    token_key: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )


config = Config()
