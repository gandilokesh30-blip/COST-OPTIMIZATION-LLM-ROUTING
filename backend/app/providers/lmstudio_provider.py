import time
import httpx
from .base import Generation
from ..config import settings

class LMStudioProvider:
    name = "LM Studio"

    def __init__(self, model: str | None = None):
        self.model_identifier = model or settings.lmstudio_model

    async def available(self) -> bool:
        if not self.model_identifier:
            return False
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(f"{settings.lmstudio_base_url.rstrip('/')}/models")
            if not response.is_success:
                return False
            models = response.json().get("data", [])
            return any(model.get("id") == self.model_identifier for model in models)
        except (httpx.HTTPError, ValueError):
            return False

    async def generate(self, prompt: str) -> Generation:
        if not self.model_identifier:
            raise RuntimeError("LMSTUDIO_MODEL is not configured")
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(
                    f"{settings.lmstudio_base_url.rstrip('/')}/chat/completions",
                    json={"model": self.model_identifier, "messages": [{"role": "user", "content": prompt}]},
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise RuntimeError("LM Studio request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError("LM Studio is unavailable") from exc
        text = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = payload.get("usage") or {}
        return Generation(text, usage.get("prompt_tokens", max(1, len(prompt) // 4)), usage.get("completion_tokens", max(1, len(text) // 4)), time.perf_counter() - start)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0