import unittest

from app.config import resolve_model_name
from pydantic import BaseModel

from app.openrouter import StructuredOutputClient


class DummyResponseModel(BaseModel):
    answer: str


class FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeCompletionResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class StructuredOutputClientTest(unittest.TestCase):
    def test_resolve_model_name_accepts_short_aliases(self):
        self.assertEqual(resolve_model_name("gpt-oss-120b", "unused"), "openai/gpt-oss-120b:free")
        self.assertEqual(resolve_model_name("Qwen3.5-122B-A10B", "unused"), "qwen/qwen3.5-122b-a10b")

    def test_generate_uses_primary_model_first(self):
        client = StructuredOutputClient()
        client._enabled = True
        completions = FakeCompletions([FakeCompletionResponse('{"answer":"ok"}')])
        client._client = type("FakeClient", (), {"chat": type("Chat", (), {"completions": completions})()})()

        response = client.generate(
            schema_name="dummy_response",
            response_model=DummyResponseModel,
            system_prompt="system",
            user_prompt="user",
        )

        self.assertEqual(response.answer, "ok")
        self.assertEqual(completions.calls[0]["model"], "openai/gpt-oss-120b:free")

    def test_generate_falls_back_to_secondary_model(self):
        client = StructuredOutputClient()
        client._enabled = True
        completions = FakeCompletions(
            [
                RuntimeError("primary failed"),
                FakeCompletionResponse('{"answer":"fallback"}'),
            ]
        )
        client._client = type("FakeClient", (), {"chat": type("Chat", (), {"completions": completions})()})()

        response = client.generate(
            schema_name="dummy_response",
            response_model=DummyResponseModel,
            system_prompt="system",
            user_prompt="user",
        )

        self.assertEqual(response.answer, "fallback")
        self.assertEqual(completions.calls[0]["model"], "openai/gpt-oss-120b:free")
        self.assertEqual(completions.calls[1]["model"], "qwen/qwen3.5-122b-a10b")


if __name__ == "__main__":
    unittest.main()
