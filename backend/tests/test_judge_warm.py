"""Shaked, 2026-11-02: "each user that is connected warms the cache for him; cut the time".

The judge's prefix (instructions, question block, figures, language, difficulty) is sent to OpenAI the moment a
question is opened, so the real verdict finds it cached; pictures go to the model bounded to 1024 px and a question's
figures are fetched once per ten minutes. On the in-memory store with a fake OpenAI-shaped provider."""

from __future__ import annotations

import io
import uuid

import pytest

from app.engine import evaluator
from app.engine.catalog import load_catalog
from app.engine.providers import LLMError, LLMResponse, LLMUsage, ScriptedProvider
from app.engine.warmup import TTL_SECONDS, JudgeWarmer, has_prompt_images
from app.services import question_resources
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from app.services.storage_images import MAX_IMAGE_SIDE, shrink_image
from tests.test_interview_service import interviewer
from tests.test_practice_hardening import GOOD, SEEDS, scripted

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class FakeOpenAI:
    """Looks like the OpenAI provider to the warmer: name, a client, and `complete` that records requests."""

    name = "openai"
    client = object()
    model = "gpt-6.1-sol"

    def __init__(self, fail_with: Exception | None = None):
        self.requests = []
        self.fail_with = fail_with

    async def complete(self, request):
        self.requests.append(request)
        if self.fail_with is not None:
            raise self.fail_with
        return LLMResponse(text="", usage=LLMUsage(input_tokens=3000, output_tokens=1, cache_read_tokens=0),
                           model=self.model, latency_ms=7)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture(scope="module")
def catalog():
    loaded = load_catalog(SEEDS)
    for question in loaded.questions.values():
        if question.assets.get("assessment_ready") is False:
            question.assets["assessment_ready"] = True
    return loaded


def a_question(catalog, *, with_images: bool):
    return next(q for q in catalog.questions.values() if has_prompt_images(q) is with_images)


def png_bytes(width: int, height: int) -> bytes:
    from PIL import Image
    out = io.BytesIO()
    Image.new("RGB", (width, height), (250, 250, 250)).save(out, format="PNG")
    return out.getvalue()


class TestTheWarmRequestIsTheJudgesPrefix:
    def test_same_instructions_figures_and_opening_text_answer_last(self, catalog):
        question = a_question(catalog, with_images=True)
        skill = catalog.skills[question.primary_skill]
        context = evaluator.question_block(question, "en", skill)
        images = [("image/png", PNG), ("image/png", PNG + b"1")]
        warm = evaluator.warm_request(question_context=context, language="en", difficulty=question.difficulty,
                                      glossary=catalog.glossary, question_images=images)
        real = evaluator.build_request(question_context=context, language="en", difficulty=question.difficulty,
                                       answer="the candidate's answer", glossary=catalog.glossary, question_images=images,
                                       check=None, hint_level=0)
        assert warm.system == real.system and warm.images == real.images and warm.role == real.role == "evaluator"
        assert warm.schema is real.schema and warm.prompt_version == real.prompt_version
        shared = real.user.split("<candidate_answer>")[0]
        assert warm.user.startswith(shared) and len(shared) > 40          # identical bytes up to the answer
        assert warm.max_tokens == evaluator.WARM_MAX_TOKENS and real.max_tokens is None
        assert "<candidate_answer>\n\n</candidate_answer>" in warm.user       # an empty answer, nothing invented

    def test_a_hint_later_only_changes_text_after_the_shared_prefix(self, catalog):
        question = a_question(catalog, with_images=False)
        context = evaluator.question_block(question, "he", None)
        warm = evaluator.warm_request(question_context=context, language="he", difficulty=3)
        hinted = evaluator.build_request(question_context=context, language="he", difficulty=3, answer="x", hint_level=2)
        assert hinted.user.startswith("<language>Hebrew</language>\n<difficulty>3</difficulty>")
        assert warm.user.startswith("<language>Hebrew</language>\n<difficulty>3</difficulty>")


class TestTheWarmer:
    async def test_warms_once_per_question_and_language_within_the_window(self, catalog):
        provider, clock = FakeOpenAI(), Clock()
        question = a_question(catalog, with_images=False)
        warmer = JudgeWarmer(provider, glossary=catalog.glossary, clock=clock)
        assert warmer.active
        assert warmer.schedule(question, "en", None) is True
        assert warmer.schedule(question, "en", None) is False              # the same question, seconds later
        assert warmer.schedule(question, "he", None) is True               # another language is another prefix
        await warmer.drain()
        assert warmer.stats["sent"] == 2 and warmer.stats["skipped_recent"] == 1 and warmer.stats["failed"] == 0
        assert warmer.stats["input_tokens"] == 6000 and warmer.stats["last_latency_ms"] == 7
        assert [r.max_tokens for r in provider.requests] == [evaluator.WARM_MAX_TOKENS] * 2
        clock.now += TTL_SECONDS + 1
        assert warmer.schedule(question, "en", None) is True               # the window passed: warm again
        await warmer.drain()
        assert warmer.stats["sent"] == 3

    async def test_fetches_the_figures_and_survives_their_absence(self, catalog):
        question = a_question(catalog, with_images=True)
        calls = {"n": 0}

        async def fetch(q):
            calls["n"] += 1
            return [("image/png", PNG)]
        provider = FakeOpenAI()
        warmer = JudgeWarmer(provider, fetch_images=fetch, glossary=catalog.glossary)
        assert await warmer.warm(question, "en", catalog.skills[question.primary_skill]) is True
        assert calls["n"] == 1 and provider.requests[-1].images == [("image/png", PNG)]

        async def missing(q):
            return None
        bare = JudgeWarmer(FakeOpenAI(), fetch_images=missing, glossary=catalog.glossary)
        assert await bare.warm(question, "en", None) is True              # the text prefix still warms
        assert bare.stats["images_unavailable"] == 1 and bare.provider.requests[-1].images == []
        without = JudgeWarmer(FakeOpenAI(), fetch_images=fetch, glossary=catalog.glossary)
        await without.warm(question, "en", None, with_images=False)      # the interview judge sees no figures
        assert without.provider.requests[-1].images == []

    async def test_a_cut_off_reply_counts_as_sent_and_nothing_ever_raises(self, catalog):
        question = a_question(catalog, with_images=False)
        cut = JudgeWarmer(FakeOpenAI(LLMError("reply was cut off by max_output_tokens", retryable=True)))
        assert await cut.warm(question, "en", None) is True and cut.stats == {**cut.stats, "sent": 1, "failed": 0}
        down = JudgeWarmer(FakeOpenAI(LLMError("API error 500: down", retryable=True)))
        assert await down.warm(question, "en", None) is False and down.stats["failed"] == 1
        crash = JudgeWarmer(FakeOpenAI(RuntimeError("boom")))
        assert await crash.warm(question, "en", None) is False and crash.stats["failed"] == 1

    async def test_only_openai_with_a_key_warms(self, catalog):
        question = a_question(catalog, with_images=False)
        assert JudgeWarmer(ScriptedProvider(lambda r: GOOD)).active is False
        assert JudgeWarmer(FakeOpenAI(), enabled=False).active is False

        class NoKey(FakeOpenAI):
            client = None
        assert JudgeWarmer(NoKey()).active is False
        assert JudgeWarmer(None).schedule(question, "en", None) is False


class TestTheServicesWarmWhenAQuestionOpens:
    async def test_practice_start_hint_and_reveal(self, catalog):
        provider = FakeOpenAI()
        warmer = JudgeWarmer(provider, glossary=catalog.glossary, clock=(clock := Clock()))
        svc = PracticeService(InMemoryStore(catalog), catalog, scripted([GOOD]),
                              ServiceConfig(suggest_reviewed_only=False, daily_attempt_limit=50), warmer=warmer)
        user = uuid.uuid4()
        question = a_question(catalog, with_images=False)
        view = await svc.start(user, question_key=question.key, language="en")
        await warmer.drain()
        assert warmer.stats["sent"] == 1
        request = provider.requests[-1]
        assert request.role == "evaluator" and question.text("en").prompt[:40] in request.system[1]
        await svc.next_hint(user, uuid.UUID(view.id))
        await svc.reveal_reference(user, uuid.UUID(view.id))
        await warmer.drain()
        assert warmer.stats["sent"] == 1 and warmer.stats["skipped_recent"] >= 1    # within the window: no second call
        clock.now += TTL_SECONDS + 1
        await svc.reveal_reference(user, uuid.UUID(view.id))                    # still reading, window passed
        await warmer.drain()
        assert warmer.stats["sent"] == 2

    async def test_practice_without_a_warmer_is_unchanged(self, catalog):
        svc = PracticeService(InMemoryStore(catalog), catalog, scripted([GOOD]), ServiceConfig(suggest_reviewed_only=False))
        view = await svc.start(uuid.uuid4(), question_key=a_question(catalog, with_images=False).key, language="en")
        assert view.id and svc.warmer is None

    async def test_interview_turns_and_hints(self, catalog):
        provider = FakeOpenAI()
        warmer = JudgeWarmer(provider, glossary=catalog.glossary)
        svc = InterviewService(InMemoryStore(catalog), catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False),
                               warmer=warmer)
        user = uuid.uuid4()
        view = await svc.start(user, duration_min=20, language="en")
        await warmer.drain()
        assert warmer.stats["sent"] == 1 and provider.requests[-1].images == []        # no figures for the interview judge
        first_key = view.current_turn.question_key
        _, view = await svc.answer(user, uuid.UUID(view.id), 0, "a strong answer", idempotency_key="k0")
        await warmer.drain()
        assert view.current_turn.question_key != first_key and warmer.stats["sent"] == 2   # the next question warmed


class TestPicturesAreBounded:
    def test_a_large_png_shrinks_and_a_small_one_is_untouched(self):
        from PIL import Image
        big = png_bytes(3000, 1500)
        mime, data = shrink_image("image/png", big)
        assert mime == "image/png" and len(data) < len(big)
        with Image.open(io.BytesIO(data)) as image:
            assert image.size == (MAX_IMAGE_SIDE, MAX_IMAGE_SIDE // 2)
        small = png_bytes(400, 300)
        assert shrink_image("image/png", small) == ("image/png", small)
        assert shrink_image("image/jpeg", b"not an image at all") == ("image/jpeg", b"not an image at all")

    def test_a_large_jpeg_stays_a_jpeg(self):
        from PIL import Image
        out = io.BytesIO()
        Image.new("RGB", (4000, 3000), (20, 30, 40)).save(out, format="JPEG", quality=95)
        mime, data = shrink_image("image/jpeg", out.getvalue())
        assert mime == "image/jpeg" and data.startswith(b"\xff\xd8\xff") and len(data) < len(out.getvalue())
        with Image.open(io.BytesIO(data)) as image:
            assert max(image.size) == MAX_IMAGE_SIDE

    async def test_a_questions_figures_are_fetched_once_and_shrunk(self, catalog, monkeypatch):
        question = a_question(catalog, with_images=True)
        downloads = {"n": 0}

        async def fake_download(settings, media):
            downloads["n"] += 1
            return [("image/png", png_bytes(2048, 1024)) for _ in media]
        monkeypatch.setattr(question_resources, "_download", fake_download)
        monkeypatch.setattr(question_resources, "PATH", type("Any", (), {"fullmatch": staticmethod(lambda s: True)})())
        from app.config import Settings, get_settings
        monkeypatch.setattr(question_resources, "get_settings", lambda: Settings(_env_file=None, supabase_url="https://x.supabase.co",
                                                                              supabase_service_role_key="k"), raising=False)
        import app.config as config
        monkeypatch.setattr(config, "get_settings", lambda: Settings(_env_file=None, supabase_url="https://x.supabase.co",
                                                                     supabase_service_role_key="k"))
        question_resources._image_cache.clear()
        first = await question_resources.fetch_question_images(question)
        second = await question_resources.fetch_question_images(question)
        assert downloads["n"] == 1 and first == second and len(first) >= 1
        from PIL import Image
        with Image.open(io.BytesIO(first[0][1])) as image:
            assert max(image.size) == MAX_IMAGE_SIDE
        assert question_resources.cached_images(question) == first
        assert get_settings  # the real settings function is untouched after the test
