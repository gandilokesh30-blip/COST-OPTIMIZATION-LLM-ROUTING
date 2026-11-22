from ..providers.lmstudio_provider import LMStudioProvider
from ..providers.openai_provider import OpenAIProvider
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.gemini_provider import GeminiProvider

async def execute(identifier: str, prompt: str):
    providers = {p.model_identifier: p for p in [LMStudioProvider(), OpenAIProvider(), AnthropicProvider(), GeminiProvider()] if p.model_identifier}
    provider = providers.get(identifier)
    if not provider or not await provider.available(): raise RuntimeError(f"Provider for {identifier} is unavailable")
    return await provider.generate(prompt)
