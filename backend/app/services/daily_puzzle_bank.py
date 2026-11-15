"""The daily game uses only standalone adaptations of alternate interview prompts.

The manifest ties each bilingual puzzle and its worked answer to a particular
localized variant. A missing variant is a content error: never substitute the
main interview prompt or its reference solution.
"""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.engine.catalog import Catalog
from app.schemas.bank import LANGUAGES


@dataclass(frozen=True)
class DailyPuzzleEntry:
    id: str
    available_from: date
    source_question_key: str
    subject: str
    title: dict[str, str]
    prompt: dict[str, str]
    solution: dict[str, str]


def load_daily_bank(catalog: Catalog, seeds_dir: Path) -> tuple[DailyPuzzleEntry, ...]:
    batches = json.loads((seeds_dir / "daily_puzzles.json").read_text(encoding="utf-8"))
    entries = []
    seen_ids = set()
    seen_sources = set()
    for batch in batches:
        available_from = date.fromisoformat(batch["available_from"])
        for item in batch["puzzles"]:
            puzzle_id = item["id"]
            source_key = item["source_question_key"]
            variant_key = item["variant_key"]
            source = catalog.questions.get(source_key)
            if source is None or source.status not in ("published", "trial"):
                raise ValueError(f"{puzzle_id}: missing or inactive source question {source_key}")
            if puzzle_id in seen_ids or (source_key, variant_key) in seen_sources:
                raise ValueError(f"{puzzle_id}: duplicate puzzle ID or source variant")
            resource = source.assets["preparation_resource"]["learner_material"]
            variants = resource.get("prompt_variants", {})
            for lang in LANGUAGES:
                localized = variants.get(lang)
                localized_key = item.get("variant_key_he", variant_key) if lang == "he" else variant_key
                variant = localized.get(localized_key) if isinstance(localized, dict) else None
                original = variant.get("prompt") if isinstance(variant, dict) else variant
                if not isinstance(original, str) or not original.strip():
                    raise ValueError(f"{puzzle_id}: missing {lang} variant {localized_key}")
                text = item[lang]
                if not all(isinstance(text.get(k), str) and text[k].strip() for k in ("title", "prompt", "solution")):
                    raise ValueError(f"{puzzle_id}: incomplete {lang} text")
                if text["prompt"].strip() == source.translations[lang].prompt.strip():
                    raise ValueError(f"{puzzle_id}: main question cannot be used as a daily puzzle")
            entries.append(DailyPuzzleEntry(
                id=puzzle_id,
                available_from=available_from,
                source_question_key=source_key,
                subject=source.subject,
                title={lang: item[lang]["title"] for lang in LANGUAGES},
                prompt={lang: item[lang]["prompt"] for lang in LANGUAGES},
                solution={lang: item[lang]["solution"] for lang in LANGUAGES},
            ))
            seen_ids.add(puzzle_id)
            seen_sources.add((source_key, variant_key))
    if not entries:
        raise ValueError("The daily puzzle bank is empty")
    return tuple(entries)
