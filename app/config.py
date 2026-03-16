import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://frigo:frigo@localhost:5432/frigo")
    model_name: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    app_env: str = os.getenv("APP_ENV", "development")


settings = Settings()
