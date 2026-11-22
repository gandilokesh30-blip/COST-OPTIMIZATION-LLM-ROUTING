import time
from openai import AsyncOpenAI
from .base import Generation
from ..config import settings

class OpenAIProvider:
    name = "OpenAI"
    def __init__(self): self.model_identifier = settings.openai_model
    async def available(self) -> bool: return bool(settings.openai_api_key)
    async def generate(self, prompt: str) -> Generation:
        start = time.perf_counter()
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        result = await client.chat.completions.create(model=self.model_identifier, messages=[{"role":"user","content":prompt}])
        text = result.choices[0].message.content or ""
        usage = result.usage
        return Generation(text, usage.prompt_tokens if usage else len(prompt)//4, usage.completion_tokens if usage else len(text)//4, time.perf_counter()-start)
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float: return input_tokens * 0.00000015 + output_tokens * 0.0000006
