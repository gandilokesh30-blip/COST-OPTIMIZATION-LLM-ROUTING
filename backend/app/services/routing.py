from dataclasses import dataclass
from ..config import settings
from .analysis import Analysis

@dataclass
class Candidate:
    key: str
    provider: str
    identifier: str
    type: str
    capability: int
    cost_input: float
    cost_output: float
    local: bool
    available: bool = True

@dataclass
class Decision:
    selected: Candidate
    score: float
    reason: str
    alternatives: list[dict]

def route(analysis: Analysis, candidates: list[Candidate], mode: str = "AUTO", preference: str = "BALANCED") -> Decision:
    if mode != "AUTO":
        matches = [c for c in candidates if c.type == mode]
        if matches: candidates = matches
    required = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}[analysis.complexity]
    scored = []
    for c in candidates:
        if not c.available: continue
        capability = 1 - min(1, abs(c.capability - required) / 3)
        privacy = 1 if analysis.privacy != "HIGH" or c.local else 0
        cost = 1 if c.local else max(0, 1 - (c.cost_input + c.cost_output) * 100000)
        latency = 1 if c.local else 0.65
        score = capability * settings.quality_weight + privacy * settings.privacy_weight + cost * settings.cost_weight + latency * settings.latency_weight
        if preference == "LOWEST_COST": score += cost * 0.35
        elif preference == "HIGHEST_QUALITY": score += (c.capability / 3) * 0.8
        elif preference == "FASTEST": score += latency * 0.35
        if required == 3 and c.capability < 3:
            score -= 0.35
        if required == 1 and c.local:
            score += 0.10
        scored.append((score, c))
    if not scored: raise RuntimeError("No available model matches the request")
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = scored[0][1]
    reason = f"Selected {selected.type} for {analysis.task_type.lower()} task: {analysis.complexity.lower()} complexity, {analysis.privacy.lower()} privacy, {preference.lower().replace('_', ' ')} preference, score {scored[0][0]:.3f}."
    return Decision(selected, round(scored[0][0], 3), reason, [{"model": c.identifier, "score": round(s, 3)} for s, c in scored[1:]])
