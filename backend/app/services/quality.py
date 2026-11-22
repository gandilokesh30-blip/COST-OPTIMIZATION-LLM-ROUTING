import re
from dataclasses import dataclass
@dataclass
class Quality:
    quality_score: float
    confidence_score: float

def evaluate(prompt: str, answer: str) -> Quality:
    if not answer.strip(): return Quality(0.0, 0.0)
    overlap = len(set(re.findall(r"\w+", prompt.lower())) & set(re.findall(r"\w+", answer.lower()))) / max(1, len(set(re.findall(r"\w+", prompt.lower()))))
    completeness = min(1.0, len(answer) / max(120, len(prompt) * 0.6))
    score = min(1.0, 0.35 + overlap * 0.35 + completeness * 0.30)
    return Quality(round(score, 3), round(min(1.0, score + 0.08), 3))
