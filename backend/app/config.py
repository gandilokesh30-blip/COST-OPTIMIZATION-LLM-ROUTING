from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = f"sqlite:///{(Path(__file__).resolve().parents[1] / 'router.db').as_posix()}"
    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_model: str = ""
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-haiku-latest"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    quality_threshold: float = 0.70
    max_escalations: int = 1
    cost_weight: float = 0.25
    quality_weight: float = 0.30
    latency_weight: float = 0.20
    privacy_weight: float = 0.25
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")

settings = Settings()
