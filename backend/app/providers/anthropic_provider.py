import time
from anthropic import AsyncAnthropic
from .base import Generation
from ..config import settings

class AnthropicProvider:
    name = "Anthropic"
    def __init__(self): self.model_identifier = settings.anthropic_model
    async def available(self) -> bool: return bool(settings.anthropic_api_key)
    async def generate(self, prompt: str) -> Generation:
        start = time.perf_counter()
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        result = await client.messages.create(model=self.model_identifier, max_tokens=4096, messages=[{"role":"user","content":prompt}])
        text = "".join(block.text for block in result.content if hasattr(block, "text"))
        return Generation(text, result.usage.input_tokens, result.usage.output_tokens, time.perf_counter()-start)
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float: return input_tokens * 0.0000008 + output_tokens * 0.000004
