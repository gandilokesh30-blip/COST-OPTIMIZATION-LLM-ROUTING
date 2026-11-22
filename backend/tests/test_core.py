import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.analysis import analyze, decompose
from app.services.quality import evaluate
from app.services.routing import Candidate, route

def models():
    return [Candidate("local", "LM Studio", "local", "LOCAL", 1, 0, 0, True), Candidate("medium", "OpenAI", "medium", "MEDIUM", 2, .000001, .000002, False), Candidate("strong", "Anthropic", "strong", "STRONG", 3, .000002, .000004, False)]

def test_analyzer_detects_coding_and_complexity():
    result = analyze("Debug this Python algorithm and optimize its time complexity")
    assert result.task_type == "Debugging"
    assert result.complexity == "HIGH"
    assert result.coding == 1

def test_decompose_multi_part():
    assert len(decompose("Explain Python, write code, and compare Java")) == 3

def test_router_prefers_local_for_simple_request():
    decision = route(analyze("What is Python?"), models())
    assert decision.selected.type == "LOCAL"

def test_router_prefers_strong_for_complex_request():
    decision = route(analyze("Analyze and optimize this algorithm"), models())
    assert decision.selected.type == "STRONG"

def test_quality_is_bounded():
    result = evaluate("Explain APIs", "An API is an interface that lets software communicate.")
    assert 0 <= result.quality_score <= 1

def test_inactive_models_are_excluded():
    options = models()
    options[0].available = False
    assert route(analyze("What is Python?"), options).selected.type != "LOCAL"

def test_preferences_change_selection_pressure():
    options = models()
    assert route(analyze("What is Python?"), options, preference="HIGHEST_QUALITY").selected.type == "STRONG"
    assert route(analyze("What is Python?"), options, preference="LOWEST_COST").selected.type == "LOCAL"
