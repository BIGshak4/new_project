"""The daily game uses only standalone adaptations of alternate interview prompts.

Each bilingual puzzle has its own worked answer and a link to the alternate
wording or secondary interview screenshot it adapts.
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
    start_puzzle_rotation: bool = False


def _source_variant(localized: dict | list, key: str, lang: str) -> str | None:
    if isinstance(localized, list):
        for record in localized:
            if not isinstance(record, dict):
                continue
            prompt = record.get("prompt") or record.get("original_prompt" if lang == "he" else "translation_en")
            if not prompt:
                continue
            identifier = record.get("key") or record.get("id") or record.get("source_path") or prompt.splitlines()[0]
            if identifier == key:
                return prompt
        return None
    if isinstance(localized, dict):
        record = localized.get(key)
        return record.get("prompt") if isinstance(record, dict) else record if isinstance(record, str) else None
    return None


def load_daily_bank(catalog: Catalog, seeds_dir: Path) -> tuple[DailyPuzzleEntry, ...]:
    batches = json.loads((seeds_dir / "daily_puzzles.json").read_text(encoding="utf-8"))
    entries = []
    seen_ids = set()
    seen_sources = set()
    seen_prompts = {lang: set() for lang in LANGUAGES}
    for batch in batches:
        available_from = date.fromisoformat(batch["available_from"])
        for item in batch["puzzles"]:
            puzzle_id = item["id"]
            source_key = item["source_question_key"]
            variant_key = item.get("variant_key")
            duplicate_source = item.get("duplicate_source")
            if bool(variant_key) == bool(duplicate_source):
                raise ValueError(f"{puzzle_id}: expected exactly one source variant or duplicate screenshot")
            source = catalog.questions.get(source_key)
            if source is None or source.status not in ("published", "trial"):
                raise ValueError(f"{puzzle_id}: missing or inactive source question {source_key}")
            # A multipart source can contribute independent challenges such as
            # memory capacity and detecting address aliases.
            source_part = (source_key, variant_key or duplicate_source, item.get("variant_part"))
            if puzzle_id in seen_ids or source_part in seen_sources:
                raise ValueError(f"{puzzle_id}: duplicate puzzle ID or source variant")
            resource = source.assets["preparation_resource"]
            if duplicate_source:
                secondary_questions = {
                    record.get("path") for record in resource["sources"][1:]
                    if "companion" not in record.get("role", "") and "diagram" not in record.get("role", "")
                }
                if duplicate_source not in secondary_questions or duplicate_source == resource["sources"][0].get("path"):
                    raise ValueError(f"{puzzle_id}: missing secondary question screenshot {duplicate_source}")
            variants = resource["learner_material"].get("prompt_variants", {})
            for lang in LANGUAGES:
                if variant_key:
                    localized_key = item.get("variant_key_he", variant_key) if lang == "he" else variant_key
                    original = _source_variant(variants.get(lang), localized_key, lang)
                    if not isinstance(original, str) or not original.strip():
                        raise ValueError(f"{puzzle_id}: missing {lang} variant {localized_key}")
                text = item[lang]
                if not all(isinstance(text.get(k), str) and text[k].strip() for k in ("title", "prompt", "solution")):
                    raise ValueError(f"{puzzle_id}: incomplete {lang} text")
                if text["prompt"].strip() == source.translations[lang].prompt.strip():
                    raise ValueError(f"{puzzle_id}: main question cannot be used as a daily puzzle")
                prompt = " ".join(text["prompt"].split()).casefold()
                if prompt in seen_prompts[lang]:
                    raise ValueError(f"{puzzle_id}: duplicate {lang} puzzle prompt")
                seen_prompts[lang].add(prompt)
            entries.append(DailyPuzzleEntry(
                id=puzzle_id,
                available_from=available_from,
                source_question_key=source_key,
                subject=source.subject,
                title={lang: item[lang]["title"] for lang in LANGUAGES},
                prompt={lang: item[lang]["prompt"] for lang in LANGUAGES},
                solution={lang: item[lang]["solution"] for lang in LANGUAGES},
                start_puzzle_rotation=batch.get("start_puzzle_rotation", False),
            ))
            seen_ids.add(puzzle_id)
            seen_sources.add(source_part)
    if not entries:
        raise ValueError("The daily puzzle bank is empty")
    return tuple(entries)
