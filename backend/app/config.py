"""Settings, read from the environment and from backend/.env (never committed)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase Postgres. Use the "Session pooler" or direct connection string from
    # Project Settings -> Database, with the scheme changed to postgresql+asyncpg://
    database_url: str | None = None

    # manual = prompts are written to files and a person (or Claude Code) writes the replies.
    # anthropic = the real API; needs ANTHROPIC_API_KEY.
    llm_provider: str = "manual"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-5"
    anthropic_enable_fallbacks: bool = True

    seeds_dir: Path = BACKEND_DIR / "seeds"
    workdir: Path = BACKEND_DIR / "workdir"

    # Development only: serve questions that are still in review or lack a parity check.
    # Production serves published, parity-checked questions and nothing else.
    allow_in_review_content: bool = False

    default_language: str = "en"
    default_role: str = "digital-hardware-engineer"
    default_company: str = "generic"


@lru_cache
def get_settings() -> Settings:
    return Settings()
