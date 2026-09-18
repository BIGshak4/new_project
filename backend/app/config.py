"""Settings, read from the environment and from backend/.env (never committed)."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    # development | staging | production. Production refuses to start without the settings it needs.
    env: str = "development"

    # Supabase Postgres. Use the "Session pooler" or direct connection string from
    # Project Settings -> Database, with the scheme changed to postgresql+asyncpg://
    database_url: str | None = None

    # Supabase Auth. Login tokens are verified against the project's public signing keys
    # (SUPABASE_URL/auth/v1/.well-known/jwks.json). SUPABASE_JWT_SECRET is only for projects
    # still on the legacy shared-secret (HS256) setup.
    supabase_url: str | None = None
    supabase_jwt_secret: str | None = None
    # Only e-mails listed in Harel's jr_members table may use the practice API during the pilot.
    require_pilot_membership: bool = True

    # Browser origins allowed to call the API directly (the Netlify sites). Comma-separated.
    allowed_origins: Annotated[list[str], NoDecode] = []      # plain comma-separated, not JSON
    # Attempts a user may start per UTC day. Fails gracefully with 429, never silently.
    daily_attempt_limit: int = 30

    # scripted  = instant fake evaluations, for building and demoing the web app without a key.
    # manual    = prompts are written to files and a person (or Claude Code) writes the replies.
    # anthropic = the real API; needs ANTHROPIC_API_KEY.
    llm_provider: str = "scripted"
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

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def database_host_kind(self) -> str | None:
        """direct | pooler | other | None. Supabase's direct host (db.<ref>.supabase.co) resolves only to
        IPv6, which Docker containers and most hosts (Render included) cannot reach; the Session pooler
        is IPv4. Found the hard way in a container."""
        if not self.database_url:
            return None
        match = re.search(r"@([^:/]+)", self.database_url)
        host = match.group(1) if match else ""
        return "direct" if host.startswith("db.") and host.endswith(".supabase.co") else "pooler" if "pooler" in host else "other"

    def production_problems(self) -> list[str]:
        """What is missing for a safe production start. Empty means go."""
        problems = []
        if not self.database_url:
            problems.append("DATABASE_URL is not set")
        elif self.database_host_kind == "direct":
            problems.append("DATABASE_URL uses the direct host (IPv6 only); use the Session pooler string")
        if not self.supabase_url:
            problems.append("SUPABASE_URL is not set (needed to verify login tokens)")
        if not self.allowed_origins:
            problems.append("ALLOWED_ORIGINS is empty (no browser could call the API)")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            problems.append("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set")
        if self.llm_provider == "manual":
            problems.append("LLM_PROVIDER=manual waits for a person to answer each model call")
        if self.llm_provider == "scripted":
            problems.append("LLM_PROVIDER=scripted returns fake evaluations")
        if self.allow_in_review_content:
            problems.append("ALLOW_IN_REVIEW_CONTENT=true would serve unreviewed questions")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()
