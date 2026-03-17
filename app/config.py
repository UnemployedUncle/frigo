import os
from dataclasses import dataclass


MODEL_ALIASES = {
    "gpt-oss-120b": "openai/gpt-oss-120b:free",
    "openai/gpt-oss-120b": "openai/gpt-oss-120b:free",
    "openai/gpt-oss-120b:free": "openai/gpt-oss-120b:free",
    "qwen3.5-122b-a10b": "qwen/qwen3.5-122b-a10b",
    "qwen/qwen3.5-122b-a10b": "qwen/qwen3.5-122b-a10b",
}


def resolve_model_name(value: str, default: str) -> str:
    candidate = (value or default).strip()
    return MODEL_ALIASES.get(candidate.lower(), candidate)


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://frigo:frigo@localhost:5432/frigo")
    model_name: str = resolve_model_name(
        os.getenv("OPENROUTER_MODEL", ""),
        "openai/gpt-oss-120b:free",
    )
    fallback_model_name: str = resolve_model_name(
        os.getenv("OPENROUTER_FALLBACK_MODEL", ""),
        "qwen/qwen3.5-122b-a10b",
    )
    app_env: str = os.getenv("APP_ENV", "development")


settings = Settings()
