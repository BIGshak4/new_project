"""What the API needs once per process: the catalog, the model provider, the store, the service.

Built in the app lifespan from settings. Tests build a Runtime with the in-memory store
and a scripted provider and put it on `app.state.runtime`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.engine.catalog import Catalog, load_catalog
from app.engine.providers import Provider, build_provider
from app.repo.fundamentals import DbFundamentalsRepository, MemoryFundamentalsRepository
from app.services.avatars import AvatarsService
from app.services.avatars import load_catalog as load_avatar_catalog
from app.services.billing import BillingConfig, BillingService, FakeStripe, HttpStripe, load_plans
from app.services.code_execution import CodeExecutionService
from app.services.coins import CoinsService
from app.services.coins import load_rules as load_coin_rules
from app.services.demo_provider import DemoProvider
from app.services.duels import DuelService, load_quiz
from app.services.fundamentals import FundamentalsService, load_fundamentals_catalog
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from app.services.storage_images import StorageImageFetcher
from app.services.store import DbStore, Store


@dataclass
class Runtime:
    catalog: Catalog
    provider: Provider
    store: Store
    practice: PracticeService
    store_kind: str                                  # database | memory
    billing: BillingService | None = None
    coins: CoinsService | None = None                # the coin ledger, the shop (and the duels' escrow)
    duels: DuelService | None = None                 # coin duels between two users
    image_fetcher: StorageImageFetcher | None = None  # set when answer photos can be read for the evaluator
    interview: InterviewService | None = None        # mock interviews
    fundamentals: FundamentalsService | None = None  # self-reported short-card history, no grading
    avatars: AvatarsService | None = None             # persistent logical-component customization and cosmetic ownership
    code_execution: CodeExecutionService | None = None

    async def aclose(self) -> None:
        # a redeploy waits a little for feedback being written; anything unfinished is resumed on the next read
        await self.practice.drain(timeout=20)
        if self.image_fetcher is not None:
            await self.image_fetcher.aclose()
        if self.code_execution is not None:
            await self.code_execution.aclose()


REAL_PROVIDERS = ("openai", "anthropic")        # a model is really called; openai is the default, anthropic the fallback


def make_provider(settings: Settings) -> Provider:
    """The provider LLM_PROVIDER names. A missing key does not raise here: the real providers fail at the first
    model call with a clear LLMError, so the app, /health and the scripts still start."""
    if settings.llm_provider == "scripted":
        return DemoProvider()
    if settings.llm_provider == "openai":
        return build_provider("openai", api_key=settings.openai_api_key, model=settings.openai_model,
                              role_models=settings.role_models)
    if settings.llm_provider == "anthropic":
        return build_provider("anthropic", api_key=settings.anthropic_api_key, model=settings.anthropic_model,
                              enable_fallbacks=settings.anthropic_enable_fallbacks, role_models=settings.role_models)
    return build_provider("manual", manual_dir=settings.workdir / "manual_llm")


def build_runtime(settings: Settings, *, catalog: Catalog | None = None, provider: Provider | None = None,
                  store: Store | None = None) -> Runtime:
    catalog = catalog or load_catalog(settings.seeds_dir)
    provider = provider or make_provider(settings)
    if store is None:
        if settings.database_url:
            store, kind = DbStore(allow_in_review=settings.allow_in_review_content), "database"
        else:
            # no database: questions from the seed files, everything else in memory (lost on restart)
            store, kind = InMemoryStore(catalog, allow_in_review=settings.allow_in_review_content), "memory"
    else:
        kind = "database" if isinstance(store, DbStore) else "memory"
    config = ServiceConfig(role=settings.default_role, company=settings.default_company,
                           default_language=settings.default_language, daily_attempt_limit=settings.daily_attempt_limit,
                           polish_tips=settings.llm_provider in REAL_PROVIDERS,
                           suggest_reviewed_only=settings.suggest_reviewed_only,
                           feedback_in_background=settings.feedback_in_background)
    fetcher = make_image_fetcher(settings)
    interview_config = InterviewConfig(role=settings.default_role, company=settings.default_company,
                                       default_language=settings.default_language,
                                       daily_limit=settings.interview_daily_limit,
                                       reviewed_only=settings.interview_reviewed_only,
                                       narrative=settings.llm_provider in REAL_PROVIDERS)
    plans = load_plans(settings.seeds_dir / "billing_plans.json",
                       {"stripe_price_regular": settings.stripe_price_regular, "stripe_price_premium": settings.stripe_price_premium})
    configured = bool(settings.stripe_secret_key)
    gateway = HttpStripe(settings.stripe_secret_key, settings.stripe_webhook_secret) if configured else FakeStripe()
    billing = BillingService(store, gateway, BillingConfig(plans=plans, require_payment=settings.require_payment,
                                                           free_option_visible=settings.billing_free_option_visible,
                                                           site_url=settings.site_url, configured=configured))
    from app.services.question_resources import fetch_question_images
    practice = PracticeService(store, catalog, provider, config, image_fetcher=fetcher,
                               question_image_fetcher=fetch_question_images)
    # the plan decides how many questions a day (regular 30, premium 50; a free user keeps the default while
    # payment is optional; Shaked, 2026-10-20)
    coins = CoinsService(store, load_coin_rules(settings.seeds_dir / "coins.json"))
    practice.coins = coins

    async def daily_limit(user_id):
        base = await billing.daily_limit(user_id, default=settings.daily_attempt_limit)
        return base + await coins.extra_questions_today(user_id)      # the shop's top-up (Shaked, 2026-10-22)

    practice.daily_limit_for = daily_limit

    async def interview_finished(tx, user_id, session_id):
        await practice._complete_program_item(tx, user_id, session_id=session_id)

    runtime = Runtime(catalog=catalog, provider=provider, store=store, practice=practice, store_kind=kind,
                   image_fetcher=fetcher, billing=billing, coins=coins,
                   avatars=AvatarsService(store, coins, load_avatar_catalog(settings.seeds_dir / "avatar_cosmetics.json")),
                   duels=DuelService(store, catalog, provider, coins, reviewed_only=settings.suggest_reviewed_only,
                                     site_url=settings.site_url, quiz=load_quiz(settings.seeds_dir / "duel_quiz.json")),
                   fundamentals=FundamentalsService(
                       DbFundamentalsRepository() if kind == "database" else MemoryFundamentalsRepository(),
                       load_fundamentals_catalog(settings.seeds_dir / "fundamentals_catalog.json")),
                   interview=InterviewService(store, catalog, provider, interview_config, image_fetcher=fetcher,
                                              on_finished=interview_finished, coins=coins))
    runtime.code_execution = CodeExecutionService(settings, database=kind == "database")
    practice.code_execution = runtime.code_execution
    runtime.interview.code_execution = runtime.code_execution
    runtime.duels.code_execution = runtime.code_execution
    return runtime


def make_image_fetcher(settings: Settings) -> StorageImageFetcher | None:
    """Photos attached to answers can only be judged when the server may read the private bucket."""
    if settings.supabase_url and settings.supabase_service_role_key:
        return StorageImageFetcher(settings.supabase_url, settings.supabase_service_role_key)
    return None
