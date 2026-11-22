from dataclasses import dataclass
from typing import Protocol

@dataclass
class Generation:
    text: str
    input_tokens: int
    output_tokens: int
    latency: float

class Provider(Protocol):
    name: str
    model_identifier: str
    async def available(self) -> bool: ...
    async def generate(self, prompt: str) -> Generation: ...
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float: ...
