import time
from google import genai
from .base import Generation
from ..config import settings


class GeminiProvider:
    name = "Gemini"

    def __init__(self):
        self.model_identifier = settings.gemini_model

    async def available(self) -> bool:
        return bool(settings.gemini_api_key and self.model_identifier)

    async def generate(self, prompt: str) -> Generation:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        start = time.perf_counter()
        client = genai.Client(api_key=settings.gemini_api_key)
        result = await client.aio.models.generate_content(
            model=self.model_identifier,
            contents=prompt,
        )
        text = result.text or ""
        usage = result.usage_metadata
        input_tokens = usage.prompt_token_count if usage else max(1, len(prompt) // 4)
        output_tokens = usage.candidates_token_count if usage else max(1, len(text) // 4)
        return Generation(text, input_tokens, output_tokens, time.perf_counter() - start)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return input_tokens * 0.0000003 + output_tokens * 0.0000025