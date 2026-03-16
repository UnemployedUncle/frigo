from typing import Optional, Type

from openai import OpenAI
from pydantic import BaseModel

from app.config import settings


class StructuredOutputClient:
    def __init__(self) -> None:
        self._enabled = bool(settings.openrouter_api_key)
        self._client = (
            OpenAI(base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key)
            if self._enabled
            else None
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def generate(
        self,
        *,
        schema_name: str,
        response_model: Type[BaseModel],
        system_prompt: str,
        user_prompt: str,
    ) -> Optional[BaseModel]:
        if not self._client:
            return None

        schema = response_model.model_json_schema()
        response = self._client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        )
        message = response.choices[0].message.content or "{}"
        return response_model.model_validate_json(message)


structured_client = StructuredOutputClient()
