import os
from typing import List
import asyncio
import tiktoken
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import tiktoken
from fastapi import HTTPException
from openai import OpenAI

load_dotenv(override=True)


class DatabaseConfig(BaseModel):
    dsn: str = "postgresql://user:password@host:port/dbname"
    async_dsn: str = "postgresql+asyncpg://user:password@host:port/dbname"


class AIConfig(BaseModel):
    openai_api_key: str
    model_name: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 200


class Config(BaseSettings):
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "MedLife Healthcare API"
    ENVIRONMENT: str = "development"
    TRUSTED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["*"]

    database: DatabaseConfig = DatabaseConfig()
    ai: AIConfig

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
# Pricing constants for gpt-3.5-turbo (change if you switch models)
INPUT_PRICE_PER_K1 = 0.0015  # $0.0015 per 1 K input tokens
OUTPUT_PRICE_PER_K1 = 0.002  # $0.002  per 1 K output tokens
PER_CALL_DOLLAR_LIMIT = 0.01  # $0.01 max per call


async def get_chat_response(messages: list[dict]) -> str:
    # 1️⃣ Count input tokens
    enc = tiktoken.encoding_for_model(config.ai.model_name)
    input_tokens = sum(len(enc.encode(m["content"])) for m in messages)

    # 2️⃣ Assume the full response budget
    output_tokens = config.ai.max_tokens

    # 3️⃣ Estimate cost
    estimated_cost = (
        input_tokens * INPUT_PRICE_PER_K1 / 1_000
        + output_tokens * OUTPUT_PRICE_PER_K1 / 1_000
    )

    # 4️⃣ Enforce your per-call budget
    if estimated_cost > PER_CALL_DOLLAR_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Estimated cost ${estimated_cost:.4f} exceeds "
                f"per-call limit of ${PER_CALL_DOLLAR_LIMIT:.2f}"
            ),
        )

    # 5️⃣ Perform the sync API call in a thread
    client = OpenAI(api_key=config.ai.openai_api_key)
    resp = await asyncio.to_thread(
        client.chat.completions.create,
        model=config.ai.model_name,
        temperature=config.ai.temperature,
        messages=messages,
        max_tokens=config.ai.max_tokens,
    )

    return resp.choices[0].message.content
