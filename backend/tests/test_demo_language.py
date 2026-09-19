import pytest

from app.engine.i18n import language_block
from app.engine.providers import LLMRequest
from app.services.demo_provider import _respond


@pytest.mark.parametrize("role", ["evaluator", "generator", "feedback", "report", "tip"])
def test_demo_respects_system_practice_language(role):
    request = LLMRequest(role=role, system=[language_block("he")], user="<candidate_answer>\nshort\n</candidate_answer>")
    hebrew = str(_respond(request))
    assert any("\u0590" <= c <= "\u05ff" for c in hebrew)
    request.system = [language_block("en")]
    request.user += language_block("he")  # Candidate text must not override practice language.
    english = str(_respond(request))
    assert not any("\u0590" <= c <= "\u05ff" for c in english)
