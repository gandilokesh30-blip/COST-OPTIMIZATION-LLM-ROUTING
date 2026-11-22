import re
from dataclasses import dataclass

@dataclass
class Analysis:
    task_type: str
    complexity: str
    reasoning: int
    coding: int
    mathematics: int
    privacy: str
    instructions: int
    subtasks: int
    context_tokens: int

def analyze(text: str, privacy_override: str = "AUTO") -> Analysis:
    lower = text.lower()
    coding = int(bool(re.search(r"\b(code|program|javascript|bug|debug|function|algorithm|implement|write)\b", lower) or re.search(r"\bpython\b", lower) and re.search(r"\b(write|code|program|function|implement|debug)\b", lower)))
    math = int(bool(re.search(r"\b(math|calculate|equation|prove|integral|probability)\b", lower)))
    reasoning = int(bool(re.search(r"\b(why|compare|analyze|reason|optimize|trade.?off|design)\b", lower)))
    privacy = privacy_override if privacy_override != "AUTO" else ("HIGH" if re.search(r"\b(password|secret|medical|health|private|confidential|personal data)\b", lower) else "LOW")
    parts = max(1, len(re.findall(r",|;|\band\b|\bthen\b", lower)) + 1)
    task = "Debugging" if "debug" in lower or "error" in lower else "Coding" if coding else "Mathematics" if math else "Research/Analysis" if reasoning else "Explanation" if re.search(r"\b(explain|how does)\b", lower) else "General Question"
    complexity = "HIGH" if reasoning + coding + math >= 2 or len(text) > 1800 else "MEDIUM" if reasoning or coding or math or len(text) > 500 else "LOW"
    if parts >= 3: task, complexity = "Multi-Part Task", "HIGH" if parts >= 4 else "MEDIUM"
    return Analysis(task, complexity, reasoning, coding, math, privacy, len(re.findall(r"\b(should|must|include|also|then)\b", lower)), parts, max(1, len(text)//4))

def decompose(text: str) -> list[str]:
    parts = [p.strip(" .") for p in re.split(r",|;|\band\b|\bthen\b", text, flags=re.I) if p.strip(" .")]
    return parts if len(parts) > 1 else [text]
