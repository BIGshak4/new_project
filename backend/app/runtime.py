"""What the API needs once per process: the catalog, the model provider, the store, the service.

Built in the app lifespan from settings. Tests build a Runtime with the in-memory store
and a scripted provider and put it on `app.state.runtime`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.engine.catalog import Catalog, load_catalog
from app.engine.providers import Provider, build_provider
from app.services.demo_provider import DemoProvider
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
    image_fetcher: StorageImageFetcher | None = None  # set when answer photos can be read for the evaluator
    interview: InterviewService | None = None        # mock interviews

    async def aclose(self) -> None:
        # a redeploy waits a little for feedback being written; anything unfinished is resumed on the next read
        await self.practice.drain(timeout=20)
        if self.image_fetcher is not None:
            await self.image_fetcher.aclose()


def make_provider(settings: Settings) -> Provider:
    if settings.llm_provider == "scripted":
        return DemoProvider()
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
                           polish_tips=settings.llm_provider == "anthropic",
                           suggest_reviewed_only=settings.suggest_reviewed_only,
                           feedback_in_background=settings.feedback_in_background)
    fetcher = make_image_fetcher(settings)
    interview_config = InterviewConfig(role=settings.default_role, company=settings.default_company,
                                       default_language=settings.default_language,
                                       daily_limit=settings.interview_daily_limit,
                                       reviewed_only=settings.interview_reviewed_only,
                                       narrative=settings.llm_provider == "anthropic")
    practice = PracticeService(store, catalog, provider, config, image_fetcher=fetcher)

    async def interview_finished(tx, user_id, session_id):
        await practice._complete_program_item(tx, user_id, session_id=session_id)

    return Runtime(catalog=catalog, provider=provider, store=store, practice=practice, store_kind=kind,
                   image_fetcher=fetcher,
                   interview=InterviewService(store, catalog, provider, interview_config, image_fetcher=fetcher,
                                              on_finished=interview_finished))


def make_image_fetcher(settings: Settings) -> StorageImageFetcher | None:
    """Photos attached to answers can only be judged when the server may read the private bucket."""
    if settings.supabase_url and settings.supabase_service_role_key:
        return StorageImageFetcher(settings.supabase_url, settings.supabase_service_role_key)
    return None
