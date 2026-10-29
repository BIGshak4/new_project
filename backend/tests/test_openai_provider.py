"""The OpenAI provider against a fake SDK client, so the code that runs once the key exists has run (2026-10-29).

Checks what is sent (model per role, instructions from the system blocks, effort, structured output, images,
the cache key) and how every SDK outcome is mapped (parsed reply, refusal, content filter, cut-off, rate limit,
5xx, 4xx, connection error, the schema fallback). No network."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import openai
import pytest

from app.config import Settings
from app.engine import evaluator
from app.engine.providers import (
    OPENAI_PRICES,
    LLMError,
    LLMRefusal,
    LLMRequest,
    LLMUsage,
    OpenAIProvider,
    build_provider,
)
from app.runtime import make_provider
from app.schemas.engine import Evaluation
from tests.conftest import make_evaluation

GOOD = make_evaluation(correctness=0.9, depth=0.8)


def fake_response(*, text: str = "", parsed=None, status: str = "completed", reason: str | None = None,
                  refusal: str | None = None, model: str = "gpt-6.1-sol-2026-09-01"):
    usage = SimpleNamespace(input_tokens=1200, output_tokens=300, input_tokens_details=SimpleNamespace(cached_tokens=1000),
                            output_tokens_details=SimpleNamespace(reasoning_tokens=120))
    parts = [SimpleNamespace(type="refusal", refusal=refusal)] if refusal else [SimpleNamespace(type="output_text", text=text)]
    return SimpleNamespace(status=status, incomplete_details=SimpleNamespace(reason=reason) if reason else None,
                           output=[SimpleNamespace(type="message", content=parts)], output_text=text, output_parsed=parsed,
                           usage=usage, model=model)


def http_error(cls, status: int, message: str = "boom"):
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(status, request=request, json={"error": {"message": message}})
    return cls(message, response=response, body={"error": {"message": message}})


@pytest.fixture
def provider():
    p = OpenAIProvider(api_key="test-key", model="gpt-6.1-sol", role_models={"feedback": "gpt-6.1-terra", "tip": "gpt-6.1-terra"})
    p.sent: list[dict] = []
    return p


def install(provider, parse_outcome=None, create_outcome=None):
    async def parse(**kwargs):
        provider.sent.append(("parse", kwargs))
        if isinstance(parse_outcome, Exception):
            raise parse_outcome
        return parse_outcome

    async def create(**kwargs):
        provider.sent.append(("create", kwargs))
        if isinstance(create_outcome, Exception):
            raise create_outcome
        return create_outcome
    provider.client.responses.parse = parse
    provider.client.responses.create = create


def request(role="evaluator", schema=Evaluation, images=()):
    return LLMRequest(role=role, system=["stable block", "question block"], user="<candidate_answer>x</candidate_answer>",
                      schema=schema, prompt_version="evaluator.v1", images=list(images))


class TestWhatIsSent:
    async def test_structured_call_shape(self, provider):
        install(provider, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD))
        response = await provider.complete(request())
        kind, sent = provider.sent[0]
        assert kind == "parse" and sent["model"] == "gpt-6.1-sol" and sent["text_format"] is Evaluation
        assert sent["instructions"] == "stable block\n\nquestion block"          # most stable first: the prefix cache
        assert sent["input"] == "<candidate_answer>x</candidate_answer>"
        assert sent["reasoning"] == {"effort": "low"} and sent["max_output_tokens"] == 8000
        assert sent["prompt_cache_key"] == "jobrun:evaluator" and sent["store"] is False
        assert response.parsed == GOOD and response.model == "gpt-6.1-sol-2026-09-01" and response.stop_reason == "completed"
        assert response.usage.input_tokens == 200 and response.usage.cache_read_tokens == 1000     # cached split out
        assert response.usage.output_tokens == 300 and response.usage.cache_write_tokens == 0
        assert response.usage.cost_usd("gpt-6.1-sol-2026-09-01") == round((200 * 2.00 + 1000 * 0.10 + 300 * 10.00) / 1e6, 6)

    async def test_effort_and_model_follow_the_role(self, provider):
        for role, effort, model in (("generator", "medium", "gpt-6.1-sol"), ("tip", "low", "gpt-6.1-terra"),
                                    ("report", "medium", "gpt-6.1-sol"), ("feedback", "low", "gpt-6.1-terra")):
            install(provider, create_outcome=fake_response(text="a polished sentence"))
            await provider.complete(LLMRequest(role=role, system=["s"], user="u", schema=None))
            kind, sent = provider.sent[-1]
            assert kind == "create" and sent["reasoning"] == {"effort": effort} and sent["model"] == model, role

    async def test_images_go_before_the_text_as_data_urls(self, provider):
        install(provider, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD))
        await provider.complete(request(images=[("image/png", b"\x89PNG")]))
        content = provider.sent[0][1]["input"][0]["content"]
        assert content[0]["type"] == "input_image" and content[0]["image_url"].startswith("data:image/png;base64,")
        assert content[-1] == {"type": "input_text", "text": "<candidate_answer>x</candidate_answer>"}

    async def test_a_dated_model_id_prices_as_its_family(self):
        assert LLMUsage(input_tokens=1_000_000).cost_usd("gpt-6-astra-2026-10-01") == OPENAI_PRICES["gpt-6-astra"][0]
        assert LLMUsage(input_tokens=1_000_000).cost_usd("gpt-unknown") is None                 # unknown is never free


class TestOutcomes:
    async def test_refusal_is_never_retried(self, provider):
        install(provider, parse_outcome=fake_response(refusal="I cannot help with that"))
        with pytest.raises(LLMRefusal):
            await provider.complete(request())

    async def test_content_filter_is_a_refusal(self, provider):
        install(provider, parse_outcome=fake_response(status="incomplete", reason="content_filter"))
        with pytest.raises(LLMRefusal):
            await provider.complete(request())

    async def test_unparsed_reply_is_parsed_from_text(self, provider):
        install(provider, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=None))
        assert (await provider.complete(request())).parsed == GOOD

    async def test_cut_off_structured_reply_is_retryable(self, provider):
        install(provider, parse_outcome=fake_response(text="{\"correct", parsed=None, status="incomplete", reason="max_output_tokens"))
        with pytest.raises(LLMError) as raised:
            await provider.complete(request())
        assert raised.value.retryable and "cut off" in str(raised.value)

    async def test_garbage_reply_is_retryable(self, provider):
        install(provider, parse_outcome=fake_response(text="not json", parsed=None))
        with pytest.raises(LLMError) as raised:
            await provider.complete(request())
        assert raised.value.retryable

    @pytest.mark.parametrize("make, retryable", [
        (lambda: http_error(openai.RateLimitError, 429), True),
        (lambda: http_error(openai.InternalServerError, 500), True),
        (lambda: http_error(openai.APIStatusError, 503), True),
        (lambda: http_error(openai.BadRequestError, 400, "bad parameter"), False),
        (lambda: http_error(openai.AuthenticationError, 401), False),
        (lambda: openai.APIConnectionError(request=httpx.Request("POST", "https://x")), True),
        (lambda: openai.APITimeoutError(request=httpx.Request("POST", "https://x")), True),
    ], ids=["429", "500", "503", "400", "401", "connection", "timeout"])
    async def test_sdk_errors_are_mapped(self, provider, make, retryable):
        install(provider, parse_outcome=make())
        with pytest.raises(LLMError) as raised:
            await provider.complete(request())
        assert raised.value.retryable is retryable and not isinstance(raised.value, LLMRefusal)


class TestSchemaFallback:
    async def test_a_400_about_the_schema_falls_back_to_json_in_text(self, provider):
        install(provider, parse_outcome=http_error(openai.BadRequestError, 400, "Invalid schema for response_format"),
                create_outcome=fake_response(text=GOOD.model_dump_json()))
        response = await provider.complete(request())
        kinds = [k for k, _ in provider.sent]
        assert kinds == ["parse", "create"] and response.parsed == GOOD and provider._schema_unsupported
        _, sent = provider.sent[1]
        assert sent["text"] == {"format": {"type": "json_object"}} and "JSON schema" in sent["input"]
        install(provider, create_outcome=fake_response(text=GOOD.model_dump_json()))
        await provider.complete(request())
        assert provider.sent[-1][0] == "create"                                   # remembered for the process


class TestThroughTheEvaluator:
    async def test_the_evaluator_scores_with_the_real_provider_class(self, provider):
        install(provider, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD))
        result = await evaluator.evaluate(provider, question_context="<question/>", known_error_keys=set(), language="en",
                                          difficulty=3, answer="alarm = (A&B)|(A&C)|(B&C)")
        assert result.ok and result.model == "gpt-6.1-sol-2026-09-01" and result.usage.cache_read_tokens == 1000
        _, sent = provider.sent[0]
        assert "<candidate_answer>" in sent["input"] and sent["instructions"].endswith("<question/>")

    async def test_one_retry_then_graceful_failure(self, provider):
        install(provider, parse_outcome=http_error(openai.InternalServerError, 500))
        result = await evaluator.evaluate(provider, question_context="<question/>", known_error_keys=set(), language="en",
                                          difficulty=3, answer="x")
        assert not result.ok and result.attempts == 2 and "eval_failed" in result.flags


class TestSettings:
    def test_openai_settings_pick_the_judge_and_the_prose_models(self):
        s = Settings(_env_file=None, llm_provider="openai", openai_api_key="k")
        assert s.judge_model == "gpt-6.1-sol" and s.role_models == {"feedback": "gpt-6.1-terra", "tip": "gpt-6.1-terra",
                                                                     "generator": "gpt-6.1-terra"}
        p = make_provider(s)
        assert isinstance(p, OpenAIProvider) and p.model_for("tip") == "gpt-6.1-terra" and p.model_for("evaluator") == "gpt-6.1-sol"
        a = Settings(_env_file=None, llm_provider="anthropic", anthropic_api_key="k")
        assert a.judge_model == "claude-opus-5-5" and a.role_models["feedback"] == "claude-sonnet-5"

    def test_openai_without_a_key_is_named_at_startup(self):
        s = Settings(_env_file=None, llm_provider="openai")
        assert any("OPENAI_API_KEY" in problem for problem in s.production_problems())

    def test_the_factory_knows_openai(self):
        assert build_provider("openai", api_key="k").name == "openai"
        with pytest.raises(ValueError):
            build_provider("gemini")
