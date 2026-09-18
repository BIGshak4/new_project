"""Build the question bank seed from Harel's example bank plus the enrichment files.

    uv run python scripts/build_example_bank.py          # writes seeds/questions/example_bank.json
    uv run python scripts/build_example_bank.py --check  # verify the generated file is up to date

Inputs
  ../example_question/questions.json            Harel's 30 questions: prompts, hints, references, translations.
                                                 Never edited here; it stays the source of the question text.
  seeds/questions/enrichment/*.json              What the engine needs on top: skills, rubric, hint levels,
                                                 common errors, accepted approaches, deterministic checks.
Output
  seeds/questions/example_bank.json              What scripts/seed_db.py loads. Generated; do not edit by hand.

Keys follow the database: "example-" + Harel's key. The `assets` block keeps every field his app
and his row-level policy rely on (collection, titles, topic, source_id, shared_code).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO = BACKEND.parent
SOURCE = REPO / "example_question" / "questions.json"
ENRICHMENT_DIR = BACKEND / "seeds" / "questions" / "enrichment"
OUTPUT = BACKEND / "seeds" / "questions" / "example_bank.json"

REVIEW_NOTE = ("Harel's example bank (in_review). Prompt, reference and one hint from example_question/questions.json; "
               "skills, rubric, hint levels 1-3, common errors and checks added by the enrichment files. "
               "Needs technical review, rubric review and Hebrew/English parity review before publishing.")


def subject_for(question: dict) -> str:
    """Harel's mapping from his topics to our six subjects (scripts/seed-example-questions.mjs)."""
    topic, category = question["topic"], question["category"]
    if "fsm" in topic or "state" in topic:
        return "fsms"
    if "timing" in topic or "clock" in topic or "sequential" in topic:
        return "sequential_logic"
    if category == "software" or "verilog" in topic or "hdl" in topic:
        return "relevant_programming"
    return "digital_fundamentals"


def load_enrichment() -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for path in sorted(ENRICHMENT_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, value in data.items():
            if key.startswith("_"):
                continue
            if key in merged:
                raise SystemExit(f"{path.name}: {key} is enriched twice")
            merged[key] = value
    return merged


def hints_for(language: str, harel_hint: str, extra: dict) -> list[str]:
    """Three levels: Harel's hint takes `hint_position`, the enrichment supplies the other two in order."""
    position = extra["hint_position"]
    added = list(extra["hints"][language])
    if len(added) != 2 or position not in (1, 2, 3):
        raise SystemExit("hints must supply exactly two extra hints and a hint_position in 1..3")
    levels = added[: position - 1] + [harel_hint] + added[position - 1:]
    return levels


def build(source: dict, enrichment: dict[str, dict]) -> list[dict]:
    questions = []
    missing = [f"example-{q['key']}" for q in source["questions"] if f"example-{q['key']}" not in enrichment]
    unknown = [k for k in enrichment if k not in {f"example-{q['key']}" for q in source["questions"]}]
    if missing or unknown:
        raise SystemExit(f"enrichment mismatch. missing: {missing} unknown: {unknown}")

    for q in source["questions"]:
        key = f"example-{q['key']}"
        extra = enrichment[key]
        translations = {}
        for language in ("en", "he"):
            t = q["translations"][language]
            translations[language] = {
                "title": t["title"],
                "prompt": t["prompt"],
                "requirements": extra["requirements"][language],
                "reference_solution": t["reference_solution"],
                "hints": hints_for(language, t["hint"], extra),
                "common_errors": {e["key"]: e[language] for e in extra["common_errors"]},
                "accepted_approaches": extra.get("accepted_approaches", {}).get(language, []),
                "parity_checked": False,
            }
        assets = {
            "collection": "jobrun_example_v1", "category": q["category"], "topic": q["topic"],
            "topic_title": q["topic_title"], "titles": {"he": q["translations"]["he"]["title"], "en": q["translations"]["en"]["title"]},
            "shared_code": q.get("shared_code"), "code_language": q.get("code_language"), "sources": q["sources"],
            "source_id": q["id"],
        }
        questions.append({
            "key": key, "version": q.get("version", 1), "status": "in_review", "origin": "original",
            "format": q["format"], "practice_modes": q["practice_modes"], "subject": subject_for(q),
            "difficulty": q["difficulty"], "estimated_minutes": q["estimated_minutes"],
            "archetype": extra["archetype"], "skills": extra["skills"],
            "rubric": [{"key": c["key"], "weight": c["weight"], "description": {"en": c["en"], "he": c["he"]}}
                       for c in extra["rubric"]],
            "common_errors": [{k: v for k, v in e.items() if k in ("key", "core", "skill", "tip_key")}
                              for e in extra["common_errors"]],
            "deterministic_check": extra.get("deterministic_check"),
            "check_self_test": extra.get("check_self_test"),
            "assets": assets,
            "source_name": (q["sources"][0]["name"] if q.get("sources") else None),
            "source_url": (q["sources"][0]["url"] if q.get("sources") else None),
            "license": "original", "reuse_status": "pending_review",
            "review_notes": REVIEW_NOTE, "exposure_risk": extra.get("exposure_risk", "low"),
            "translations": translations,
        })
    return questions


def render(questions: list[dict]) -> str:
    return json.dumps(questions, ensure_ascii=False, indent=1) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if example_bank.json is not up to date")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    text = render(build(source, load_enrichment()))
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != text:
            print(f"{OUTPUT.name} is out of date; run scripts/build_example_bank.py")
            return 1
        print(f"{OUTPUT.name} is up to date")
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(BACKEND)} with {text.count(chr(10))} lines from {source['question_count']} questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
