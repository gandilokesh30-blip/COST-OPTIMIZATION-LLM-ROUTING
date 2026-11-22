from typing import Literal
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=30000)
    mode: Literal["AUTO", "LOCAL", "MEDIUM", "STRONG"] = "AUTO"
    privacy_level: Literal["AUTO", "LOW", "MEDIUM", "HIGH"] = "AUTO"
    optimization_preference: Literal["LOWEST_COST", "BALANCED", "HIGHEST_QUALITY", "FASTEST"] = "BALANCED"
    cost_priority: float = Field(default=0.33, ge=0, le=1)
    quality_priority: float = Field(default=0.34, ge=0, le=1)
    speed_priority: float = Field(default=0.33, ge=0, le=1)

class RouteRequest(ChatRequest): pass

class EvaluationRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)

class ModelUpdate(BaseModel):
    is_active: bool | None = None
    capability: int | None = Field(default=None, ge=1, le=3)
    cost_input: float | None = Field(default=None, ge=0)
    cost_output: float | None = Field(default=None, ge=0)
    context_limit: int | None = Field(default=None, ge=1)
