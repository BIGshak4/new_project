"""The Anthropic provider against a fake SDK client, so the code that runs once the key exists has run.

Checks what is sent (model, cached system blocks, effort per role, structured output, fallbacks)
and how every SDK outcome is mapped (parsed reply, refusal, cut-off, rate limit, 5xx, 4xx,
connection error). No network."""

from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest

from app.engine import evaluator
from app.engine.providers import AnthropicProvider, LLMError, LLMRefusal, LLMRequest
from app.schemas.engine import Evaluation
from tests.conftest import make_evaluation

GOOD = make_evaluation(correctness=0.9, depth=0.8)


def fake_message(*, text: str = "", parsed=None, stop_reason: str = "end_turn", category: str | None = None):
    usage = SimpleNamespace(input_tokens=1200, output_tokens=300, cache_read_input_tokens=1000, cache_creation_input_tokens=0)
    block = SimpleNamespace(type="text", text=text, parsed_output=parsed)
    return SimpleNamespace(stop_reason=stop_reason, content=[block], parsed_output=parsed, usage=usage,
                           model="claude-opus-5", stop_details=SimpleNamespace(category=category) if category else None)


def http_error(cls, status: int):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status, request=request)
    return cls("boom", response=response, body=None)


@pytest.fixture
def provider():
    p = AnthropicProvider(api_key="test-key", model="claude-opus-5")
    p.sent: list[dict] = []
    return p


def install_parse(provider, outcome):
    async def parse(**kwargs):
        provider.sent.append(kwargs)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    provider.client.messages.parse = parse


def install_stream(provider, message):
    @asynccontextmanager
    async def stream(**kwargs):
        provider.sent.append(kwargs)

        async def final():
            return message
        yield SimpleNamespace(get_final_message=final)
    provider.client.messages.stream = stream


def request(role="evaluator", schema=Evaluation):
    return LLMRequest(role=role, system=["stable block", "question block"], user="<candidate_answer>x</candidate_answer>",
                      schema=schema, prompt_version="evaluator.v1")


class TestWhatIsSent:
    async def test_structured_call_shape(self, provider):
        install_parse(provider, fake_message(text=GOOD.model_dump_json(), parsed=GOOD))
        response = await provider.complete(request())
        sent = provider.sent[0]
        assert sent["model"] == "claude-opus-5" and sent["output_format"] is Evaluation
        assert sent["output_config"] == {"effort": "low"}                        # evaluator effort
        assert sent["max_tokens"] == 8000
        assert [b["text"] for b in sent["system"]] == ["stable block", "question block"]
        assert "cache_control" not in sent["system"][0] and sent["system"][1]["cache_control"] == {"type": "ephemeral"}
        assert sent["messages"] == [{"role": "user", "content": "<candidate_answer>x</candidate_answer>"}]
        assert sent["extra_headers"] == {"anthropic-beta": AnthropicProvider.FALLBACK_BETA}
        assert sent["extra_body"] == {"fallbacks": "default"}
        assert response.parsed == GOOD and response.model == "claude-opus-5"
        assert response.usage.input_tokens == 1200 and response.usage.cache_read_tokens == 1000
        assert response.usage.cost_usd("claude-opus-5") > 0

    async def test_effort_follows_the_role(self, provider):
        for role, effort in (("generator", "medium"), ("tip", "low"), ("report", "high"), ("feedback", "medium")):
            install_parse(provider, fake_message(text="{}", parsed=None))
            install_stream(provider, fake_message(text="a polished sentence of tip"))
            await provider.complete(LLMRequest(role=role, system=["s"], user="u", schema=None))
            assert provider.sent[-1]["output_config"] == {"effort": effort}, role

    async def test_fallbacks_can_be_switched_off(self):
        p = AnthropicProvider(api_key="k", enable_fallbacks=False)
        p.sent = []
        install_parse(p, fake_message(text=GOOD.model_dump_json(), parsed=GOOD))
        await p.complete(request())
        assert "extra_headers" not in p.sent[0] and "extra_body" not in p.sent[0]

    async def test_plain_text_goes_through_streaming(self, provider):
        install_stream(provider, fake_message(text="Next time, write the requirements as a checklist."))
        response = await provider.complete(LLMRequest(role="tip", system=["s"], user="u"))
        assert response.text.startswith("Next time") and response.parsed is None


class TestOutcomes:
    async def test_refusal_is_never_retried(self, provider):
        install_parse(provider, fake_message(stop_reason="refusal", category="harmful"))
        with pytest.raises(LLMRefusal):
            await provider.complete(request())

    async def test_unparsed_reply_is_parsed_from_text(self, provider):
        install_parse(provider, fake_message(text=GOOD.model_dump_json(), parsed=None))
        response = await provider.complete(request())
        assert response.parsed == GOOD

    async def test_cut_off_structured_reply_is_retryable(self, provider):
        install_parse(provider, fake_message(text='{"correctness": 0.', parsed=None, stop_reason="max_tokens"))
        with pytest.raises(LLMError) as raised:
            await provider.complete(request())
        assert raised.value.retryable

    async def test_garbage_reply_is_retryable(self, provider):
        install_parse(provider, fake_message(text="not json", parsed=None))
        with pytest.raises(LLMError) as raised:
            await provider.complete(request())
        assert raised.value.retryable

    @pytest.mark.parametrize("make, retryable", [
        (lambda: http_error(__import__("anthropic").RateLimitError, 429), True),
        (lambda: http_error(__import__("anthropic").APIStatusError, 500), True),
        (lambda: http_error(__import__("anthropic").APIStatusError, 529), True),
        (lambda: http_error(__import__("anthropic").APIStatusError, 400), False),
        (lambda: http_error(__import__("anthropic").APIStatusError, 401), False),
        (lambda: __import__("anthropic").APIConnectionError(request=httpx.Request("POST", "https://x")), True),
    ], ids=["429", "500", "529", "400", "401", "connection"])
    async def test_sdk_errors_are_mapped(self, provider, make, retryable):
        install_parse(provider, make())
        with pytest.raises(LLMError) as raised:
            await provider.complete(request())
        assert raised.value.retryable is retryable and not isinstance(raised.value, LLMRefusal)


class TestThroughTheEvaluator:
    async def test_the_evaluator_scores_with_the_real_provider_class(self, provider):
        install_parse(provider, fake_message(text=GOOD.model_dump_json(), parsed=GOOD))
        result = await evaluator.evaluate(provider, question_context="<question/>", known_error_keys=set(), language="en",
                                          difficulty=3, answer="alarm = (A&B)|(A&C)|(B&C)")
        assert result.ok and result.model == "claude-opus-5" and result.usage.input_tokens == 1200
        assert "<candidate_answer>" in provider.sent[0]["messages"][0]["content"]
        assert provider.sent[0]["system"][1]["text"] == "<question/>"                  # the question is the cached block

    async def test_one_retry_then_graceful_failure(self, provider):
        import anthropic
        install_parse(provider, http_error(anthropic.APIStatusError, 500))
        result = await evaluator.evaluate(provider, question_context="<question/>", known_error_keys=set(), language="en",
                                          difficulty=3, answer="x")
        assert not result.ok and result.attempts == 2 and "eval_failed" in result.flags


class TestAccountMismatches:
    """The first paid call must not fail on an optional feature the account lacks."""

    async def test_a_400_about_the_fallbacks_beta_disables_fallbacks_and_retries(self, provider):
        import anthropic
        calls = []

        async def parse(**kwargs):
            calls.append(kwargs)
            if "extra_headers" in kwargs:
                raise http_error_with_message(anthropic.APIStatusError, 400, "Unsupported beta header: server-side-fallback")
            return fake_message(text=GOOD.model_dump_json(), parsed=GOOD)
        provider.client.messages.parse = parse
        response = await provider.complete(request())
        assert response.parsed == GOOD and len(calls) == 2 and "extra_headers" not in calls[1]
        assert provider.enable_fallbacks is False                          # remembered for the rest of the process
        await provider.complete(request())
        assert len(calls) == 3 and "extra_headers" not in calls[2]

    async def test_a_400_about_the_schema_falls_back_to_json_in_text(self, provider):
        import anthropic

        async def parse(**kwargs):
            raise http_error_with_message(anthropic.APIStatusError, 400, "output_format: unsupported JSON schema keyword 'minimum'")
        provider.client.messages.parse = parse
        install_stream(provider, fake_message(text=GOOD.model_dump_json()))
        response = await provider.complete(request())
        assert response.parsed == GOOD and provider._schema_unsupported is True
        assert "JSON schema" in provider.sent[-1]["messages"][0]["content"]

    async def test_other_400s_are_still_errors(self, provider):
        import anthropic
        install_parse(provider, http_error_with_message(anthropic.APIStatusError, 400, "max_tokens too large"))
        with pytest.raises(LLMError) as raised:
            await provider.complete(request())
        assert not raised.value.retryable


def http_error_with_message(cls, status: int, message: str):
    request_ = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status, request=request_, json={"error": {"message": message}})
    return cls(message, response=response, body={"error": {"message": message}})
