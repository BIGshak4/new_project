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
        for role, effort, model in (("generator", "medium", "gpt-6.1-sol"), ("tip", "none", "gpt-6.1-terra"),
                                    ("report", "medium", "gpt-6.1-sol"), ("feedback", "none", "gpt-6.1-terra")):
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
        assert s.judge_model == "gpt-6.1-terra" and s.role_models == {"feedback": "gpt-6.1-terra", "tip": "gpt-6.1-terra",
                                                                       "generator": "gpt-6.1-terra", "report": "gpt-6.1-sol"}
        p = make_provider(s)
        assert isinstance(p, OpenAIProvider) and p.model_for("tip") == "gpt-6.1-terra"
        assert p.model_for("evaluator") == "gpt-6.1-terra" and p.model_for("report") == "gpt-6.1-sol"     # Shaked, 2026-11-08
        a = Settings(_env_file=None, llm_provider="anthropic", anthropic_api_key="k")
        assert a.judge_model == "claude-opus-5-5" and a.role_models["feedback"] == "claude-sonnet-5"

    def test_openai_without_a_key_is_named_at_startup(self):
        s = Settings(_env_file=None, llm_provider="openai")
        assert any("OPENAI_API_KEY" in problem for problem in s.production_problems())

    def test_the_factory_knows_openai(self):
        assert build_provider("openai", api_key="k").name == "openai"
        with pytest.raises(ValueError):
            build_provider("gemini")


class TestMissingKey:
    """LLM_PROVIDER=openai with an empty OPENAI_API_KEY (the state of backend/.env until the key is pasted) must not
    take down startup, /health or the scripts: the SDK raises at construction, the provider defers that to the first
    model call, like the Anthropic SDK does on its own."""

    def test_construction_without_a_key_does_not_raise(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAIProvider()
        assert provider.name == "openai" and provider.client is None

    async def test_the_first_call_fails_clearly_and_is_not_retried(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAIProvider(api_key=None)
        with pytest.raises(LLMError, match="OPENAI_API_KEY is not set") as info:
            await provider.complete(request())
        assert info.value.retryable is False and not isinstance(info.value, LLMRefusal)

    def test_the_runtime_builds_with_openai_and_no_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings(_env_file=None, llm_provider="openai", openai_api_key=None)
        p = make_provider(s)
        assert isinstance(p, OpenAIProvider) and p.client is None and p.model_for("tip") == "gpt-6.1-terra"

    def test_an_empty_key_is_no_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "")                      # what an empty OPENAI_API_KEY= line amounts to
        assert OpenAIProvider(api_key="").client is None

    def test_a_key_from_the_environment_still_counts(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        assert OpenAIProvider(api_key=None).client is not None


class TestSpeedKnobs:
    """2026-11-01 (Shaked: "lower the times"): the judge's effort and OpenAI's processing tier are host settings."""

    async def test_role_effort_overrides_the_code_default_for_that_role_only(self):
        p = OpenAIProvider(api_key="k", role_effort={"evaluator": "minimal"})
        p.sent = []
        install(p, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD),
                create_outcome=fake_response(text="a sentence"))
        await p.complete(request())
        await p.complete(LLMRequest(role="tip", system=["s"], user="u", schema=None))
        assert p.sent[0][1]["reasoning"] == {"effort": "minimal"}
        assert p.sent[1][1]["reasoning"] == {"effort": "none"}                  # the code's ROLE_EFFORT still applies (tip: none)
        assert "service_tier" not in p.sent[0][1]                               # the judge: not asked = not sent
        assert p.sent[1][1]["service_tier"] == "flex"                           # the tip: background prose, half price

    async def test_the_global_tier_covers_the_judge_and_the_background_prose_keeps_flex(self):
        p = OpenAIProvider(api_key="k", service_tier="priority")
        p.sent = []
        install(p, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD),
                create_outcome=fake_response(text="a sentence"))
        await p.complete(request())
        await p.complete(LLMRequest(role="feedback", system=["s"], user="u", schema=None))
        await p.complete(LLMRequest(role="report", system=["s"], user="u", schema=None))
        assert [sent["service_tier"] for _, sent in p.sent] == ["priority", "flex", "priority"]
        assert OpenAIProvider(api_key="k", service_tier="").service_tier is None

    async def test_the_background_prose_runs_on_flex_with_no_reasoning_by_default(self):
        """2026-11-07 (Shaked: "cut expenses"): card, tip and follow-up are written after the verdict is shown."""
        p = OpenAIProvider(api_key="k")
        p.sent = []
        install(p, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD),
                create_outcome=fake_response(text="a sentence"))
        for role in ("evaluator", "feedback", "tip", "generator", "report"):
            await p.complete(LLMRequest(role=role, system=["s"], user="u", schema=Evaluation if role == "evaluator" else None))
        by_role = {role: sent for role, (_, sent) in zip(("evaluator", "feedback", "tip", "generator", "report"), p.sent, strict=True)}
        assert by_role["evaluator"]["reasoning"] == {"effort": "low"} and "service_tier" not in by_role["evaluator"]
        assert by_role["feedback"]["reasoning"] == {"effort": "none"} and by_role["feedback"]["service_tier"] == "flex"
        assert by_role["tip"]["reasoning"] == {"effort": "none"} and by_role["tip"]["service_tier"] == "flex"
        assert by_role["generator"]["reasoning"] == {"effort": "medium"} and by_role["generator"]["service_tier"] == "flex"
        assert by_role["report"]["reasoning"] == {"effort": "medium"} and "service_tier" not in by_role["report"]

    async def test_a_role_tier_from_the_host_beats_the_code_default_and_the_global_tier(self):
        p = OpenAIProvider(api_key="k", service_tier="priority", role_service_tier={"feedback": "default", "evaluator": "flex"})
        p.sent = []
        install(p, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD),
                create_outcome=fake_response(text="a sentence"))
        await p.complete(request())
        await p.complete(LLMRequest(role="feedback", system=["s"], user="u", schema=None))
        await p.complete(LLMRequest(role="tip", system=["s"], user="u", schema=None))
        assert [sent["service_tier"] for _, sent in p.sent] == ["flex", "default", "flex"]

    async def test_flex_refused_for_capacity_is_retried_once_at_the_standard_tier(self):
        p = OpenAIProvider(api_key="k")
        p.sent = []
        calls = {"n": 0}

        async def create(**kwargs):
            p.sent.append(("create", kwargs))
            calls["n"] += 1
            if calls["n"] == 1:
                raise http_error(openai.RateLimitError, 429, "The flex tier is currently unavailable (resource_unavailable)")
            return fake_response(text="a sentence")
        p.client.responses.create = create
        r = await p.complete(LLMRequest(role="tip", system=["s"], user="u", schema=None))
        assert r.text == "a sentence" and [s["service_tier"] for _, s in p.sent] == ["flex", "default"]
        assert r.usage.service_tier == "default" and p.fallbacks["flex_to_default"] == 1
        # an ordinary rate limit on flex is still a rate limit
        calls["n"] = 0
        p.sent = []

        async def limited(**kwargs):
            p.sent.append(("create", kwargs))
            raise http_error(openai.RateLimitError, 429, "Rate limit reached for requests")
        p.client.responses.create = limited
        with pytest.raises(LLMError, match="rate limited"):
            await p.complete(LLMRequest(role="tip", system=["s"], user="u", schema=None))
        assert len(p.sent) == 1

    async def test_a_model_that_refuses_no_reasoning_gets_low_once(self):
        p = OpenAIProvider(api_key="k", role_models={"feedback": "gpt-6.1-sol"})   # sol does not take "none"
        p.sent = []
        calls = {"n": 0}

        async def create(**kwargs):
            p.sent.append(("create", kwargs))
            calls["n"] += 1
            if calls["n"] == 1 and kwargs["reasoning"] == {"effort": "none"}:
                raise http_error(openai.BadRequestError, 400, "Unsupported value: 'none' is not supported with this model. Supported values for reasoning.effort are low, medium")
            return fake_response(text="the card")
        p.client.responses.create = create
        r = await p.complete(LLMRequest(role="feedback", system=["s"], user="u", schema=None))
        assert r.text == "the card" and [s["reasoning"]["effort"] for _, s in p.sent] == ["none", "low"]
        assert p.fallbacks["effort_none_to_low"] == 1

    def test_the_role_tier_is_a_setting_and_is_validated(self):
        s = Settings(_env_file=None, llm_provider="openai", openai_api_key="k", openai_role_service_tier=" feedback=default, tip=priority ")
        assert s.role_service_tier == {"feedback": "default", "tip": "priority"}
        p = make_provider(s)
        assert p.tier_for(LLMRequest(role="feedback", system=["s"], user="u")) == "default"
        assert p.tier_for(LLMRequest(role="tip", system=["s"], user="u")) == "priority"
        assert p.tier_for(LLMRequest(role="generator", system=["s"], user="u")) == "flex"      # the code default
        assert p.tier_for(request()) is None
        bad = Settings(_env_file=None, llm_provider="openai", openai_api_key="k", openai_role_service_tier="tip=cheap")
        assert "OPENAI_ROLE_SERVICE_TIER tip='cheap'" in "\n".join(bad.production_problems())
        other = Settings(_env_file=None, llm_provider="anthropic", anthropic_api_key="k", openai_role_service_tier="tip=flex")
        assert other.role_service_tier == {}

    def test_the_knobs_are_settings_and_reach_the_provider(self):
        s = Settings(_env_file=None, llm_provider="openai", openai_api_key="k",
                     openai_role_effort=" evaluator=minimal, feedback=low ,broken", openai_service_tier="priority ")
        assert s.role_effort == {"evaluator": "minimal", "feedback": "low"} and s.service_tier == "priority"
        p = make_provider(s)
        assert p.role_effort == {"evaluator": "minimal", "feedback": "low"} and p.service_tier == "priority"
        assert p.effort_for(request()) == "minimal" and p.effort_for(request(role="tip")) == "none"
        assert not [x for x in s.production_problems() if "OPENAI_" in x and "KEY" not in x]

    def test_defaults_send_nothing_new_and_other_providers_ignore_them(self):
        s = Settings(_env_file=None, llm_provider="openai", openai_api_key="k")
        assert s.role_effort == {} and s.service_tier is None
        p = make_provider(s)
        assert p.role_effort == {} and p.service_tier is None
        a = Settings(_env_file=None, llm_provider="anthropic", anthropic_api_key="k", openai_role_effort="evaluator=minimal",
                     openai_service_tier="priority")
        assert a.role_effort == {} and a.service_tier is None and not [x for x in a.production_problems() if "OPENAI_" in x]

    def test_unknown_words_are_named_before_production_starts(self):
        s = Settings(_env_file=None, llm_provider="openai", openai_api_key="k", openai_role_effort="evaluator=turbo",
                     openai_service_tier="fast")
        problems = "\n".join(s.production_problems())
        assert "OPENAI_SERVICE_TIER='fast'" in problems and "evaluator='turbo'" in problems


class TestServiceTierPricing:
    """Priority processing bills double, flex half; the tier OpenAI reports lands on the usage record (2026-11-01)."""

    def test_priority_doubles_and_flex_halves_the_openai_price(self):
        base = LLMUsage(input_tokens=200, cache_read_tokens=1000, output_tokens=300)
        standard = base.cost_usd("gpt-6.1-sol")
        assert LLMUsage(200, 300, 1000, 0, "priority").cost_usd("gpt-6.1-sol") == round(2 * standard, 6)
        assert LLMUsage(200, 300, 1000, 0, "flex").cost_usd("gpt-6.1-sol") == round(0.5 * standard, 6)
        assert LLMUsage(200, 300, 1000, 0, "default").cost_usd("gpt-6.1-sol") == standard
        assert LLMUsage(200, 300, 1000, 0, "priority").cost_usd("claude-opus-5-5") == base.cost_usd("claude-opus-5-5")

    async def test_the_tier_openai_reports_wins_over_the_one_asked_for(self):
        p = OpenAIProvider(api_key="k", service_tier="priority")
        p.sent = []
        served = fake_response(text=GOOD.model_dump_json(), parsed=GOOD)
        served.service_tier = "default"                              # priority asked, standard served (OpenAI may downgrade)
        install(p, parse_outcome=served)
        r = await p.complete(request())
        assert r.usage.service_tier == "default" and r.usage.cost_usd(r.model) == LLMUsage(200, 300, 1000).cost_usd(r.model)
        install(p, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD))     # no field reported
        r = await p.complete(request())
        assert r.usage.service_tier == "priority" and r.usage.cost_usd(r.model) == round(2 * LLMUsage(200, 300, 1000).cost_usd(r.model), 6)

    async def test_no_tier_means_none_on_the_record(self):
        p = OpenAIProvider(api_key="k")
        p.sent = []
        install(p, parse_outcome=fake_response(text=GOOD.model_dump_json(), parsed=GOOD))
        assert (await p.complete(request())).usage.service_tier is None
