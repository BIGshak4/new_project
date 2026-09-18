"""Prompt files, practice language and glossary injection (Data_Models §17).

Prompts are product code: they live in versioned files and the version string is
recorded on every metrics row, so a scoring change can always be traced to a
prompt change (MVP_Build_Guide §11).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_VERSIONS = {"evaluator": "v1", "generator": "v1", "feedback": "v1", "tip": "v1", "report": "v1"}
LANGUAGE_NAMES = {"en": "English", "he": "Hebrew"}


@lru_cache(maxsize=32)
def _read(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8").strip()


def prompt(role: str) -> str:
    return _read(f"{role}.{PROMPT_VERSIONS[role]}.md")


def prompt_version(role: str) -> str:
    return f"{role}.{PROMPT_VERSIONS[role]}"


def language_block(language: str) -> str:
    return _read(f"language.{language if language in LANGUAGE_NAMES else 'en'}.md")


def glossary_block(glossary: list[dict] | None, language: str) -> str:
    """Terms the model must use consistently. `keep_english` terms stay English inside Hebrew text."""
    if not glossary:
        return ""
    lines = ["## Glossary"]
    for term in sorted(glossary, key=lambda t: t["key"]):
        if language == "he":
            rendering = term["en"] if term.get("keep_english") else term["he"]
            note = " (keep in English)" if term.get("keep_english") else ""
            lines.append(f"- {term['en']} -> {rendering}{note}")
        else:
            lines.append(f"- {term['en']}")
    return "\n".join(lines)


def stable_system_block(role: str, language: str, glossary: list[dict] | None = None) -> str:
    """Identical for every call of this role in this language: the first cached block."""
    parts = [prompt(role), language_block(language), glossary_block(glossary, language)]
    return "\n\n".join(part for part in parts if part)
