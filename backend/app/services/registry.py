from sqlalchemy.orm import Session
from ..config import settings
from ..models import Model
from ..providers.lmstudio_provider import LMStudioProvider
from ..providers.openai_provider import OpenAIProvider
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.gemini_provider import GeminiProvider
from .routing import Candidate

async def candidates(db: Session) -> list[Candidate]:
    providers = [LMStudioProvider(), OpenAIProvider(), AnthropicProvider(), GeminiProvider()]
    statuses = await _availability(providers)
    definitions = [
        ("LM Studio local", "LM Studio", settings.lmstudio_model, "LOCAL", 1, 0, 0, True),
        ("OpenAI medium", "OpenAI", settings.openai_model, "MEDIUM", 2, 0.00000015, 0.0000006, False),
        ("Anthropic strong", "Anthropic", settings.anthropic_model, "STRONG", 3, 0.0000008, 0.000004, False),
        ("Gemini Flash", "Gemini", settings.gemini_model, "MEDIUM", 2, 0.0000003, 0.0000025, False),
    ]
    result = []
    for i, item in enumerate(definitions):
        if not item[2]:
            continue
        model = db.query(Model).filter_by(model_identifier=item[2]).first()
        if not model:
            model = Model(name=item[0], provider=item[1], model_identifier=item[2], type=item[3], capability=item[4], cost_input=item[5], cost_output=item[6], is_local=item[7])
            db.add(model); db.flush()
        result.append(Candidate(model.model_identifier, model.provider, model.model_identifier, model.type, model.capability, model.cost_input, model.cost_output, model.is_local, statuses[i] and model.is_active))
    db.commit()
    return result

async def _availability(providers):
    values = []
    for p in providers:
        values.append(await p.available())
    return values
