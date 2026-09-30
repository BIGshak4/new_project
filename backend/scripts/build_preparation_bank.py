"""Compile the founders' preparation archive without modifying a single source file.

Run from any directory. Produces an engine seed and a content-addressed upload manifest.
Original content lives in interview_preparation; editorial additions live beside this script's inputs.
Uncalibrated questions are study-only: feedback is provisional and does not earn skill evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
BUCKET = "question-bank-media"

PRIMARY = [
    "binary_arithmetic", "estimation_sanity_checks", "estimation_sanity_checks", "edge_detection",
    "combinational_blocks", "basic_data_structures", "fsm_state_tables", "estimation_sanity_checks",
    "estimation_sanity_checks", "counters", "combinational_blocks", "estimation_sanity_checks",
    "boolean_algebra", "combinational_blocks", "truth_tables", "combinational_blocks",
    "estimation_sanity_checks", "binary_arithmetic", "arrays_and_search", "setup_hold_timing",
    "estimation_sanity_checks", "arrays_and_search", "bit_manipulation", "estimation_sanity_checks",
    "estimation_sanity_checks", "basic_data_structures", "bit_manipulation", "estimation_sanity_checks",
    "estimation_sanity_checks", "debugging_methodology", "combinational_blocks", "basic_data_structures",
    "estimation_sanity_checks", "binary_arithmetic", "arrays_and_search", "fsm_state_tables",
    "basic_data_structures",
]

# These describe author/personal-session state, never website learner activity or technical solution content.
PRIVATE_FIELDS = {"hint_history", "hint_delivery", "discussion_summary", "solution_disclosure"}


def strip_personal(value):
    if isinstance(value, dict):
        return {k: strip_personal(v) for k, v in value.items() if k not in PRIVATE_FIELDS
                and k not in {"request", "delivered_at", "delivered_on"}}
    if isinstance(value, list):
        return [strip_personal(v) for v in value]
    return value


def paths_in(value):
    if isinstance(value, str):
        yield from re.findall(r"(?:sources|diagrams|solutions)/[\w./-]+\.(?:png|sv|py|cpp|java)", value)
    elif isinstance(value, dict):
        for v in value.values():
            yield from paths_in(v)
    elif isinstance(value, list):
        for v in value:
            yield from paths_in(v)


def load():
    source = json.loads((BANK / "questions.json").read_text(encoding="utf-8-sig"))
    additions = json.loads((SEEDS / "preparation_editorial.json").read_text(encoding="utf-8"))
    skill_subject = {}
    for p in (SEEDS / "skills").glob("*.json"):
        for skill in json.loads(p.read_text(encoding="utf-8")):
            skill_subject[skill["key"]] = skill.get("parent")
    result, uploads = [], {}
    for i, original in enumerate(source["questions"]):
        q = strip_personal(original)
        ident = q["id"]
        edit = additions[ident]
        texts = {}
        for lang in ("he", "en"):
            text = q["translations"][lang]
            hints = [h["content"] for h in q.get("prepared_hints", []) if h.get("language") == lang]
            if not hints:
                hints = edit["hints"][lang]
            reference = text.get("reference_solution") or edit["reference_solution"][lang]
            texts[lang] = {
                "title": text["title"], "prompt": text["prompt"], "requirements": text["prompt"],
                "reference_solution": reference, "hints": hints,
                "common_errors": {}, "accepted_approaches": [], "parity_checked": False,
            }
        media = []
        # A sources/ file can itself be an answer, clarification or style reference.
        # Only explicit question sources belong before the reveal boundary.
        source_paths = {s["path"] for s in q["sources"] if s.get("path") and s.get("type") == "user_supplied_image"
                        and not any(word in s.get("role", "") for word in ("answer", "clarification", "reference"))}
        refs = {p for p in paths_in(q) if p.endswith('.png')}
        for field in ("solution_code_path", "solution_code_paths", "alternative_solution_code_path", "solution_model_path"):
            refs.update(paths_in(q.get(field)))
        # Include every preserved illustration for this question, including older alternatives.
        refs |= {str(p.relative_to(BANK)).replace("\\", "/")
                 for folder in ("sources", "diagrams") for p in (BANK / folder).glob(ident.lower() + "*")
                 if p.suffix == ".png"}
        descriptions = {m["path"]: m.get("description", "") for m in q.get("media_assets", []) if m.get("path")}
        for n, relative in enumerate(sorted(refs)):
            path = (BANK / relative).resolve()
            if not path.is_relative_to(BANK.resolve()) or not path.is_file():
                raise ValueError(f"{ident}: missing/unsafe asset {relative}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            storage_path = f"{ident.lower()}/{digest[:20]}-{path.name}"
            is_prompt = relative in source_paths
            media.append({"id": f"asset-{n + 1}", "path": storage_path, "filename": path.name,
                          "kind": "image" if path.suffix == ".png" else "file",
                          "role": "prompt" if is_prompt else "solution",
                          "caption": descriptions.get(relative, ""), "source_path": relative,
                          "sha256": digest})
            uploads[storage_path] = {"local_path": relative, "sha256": digest, "bytes": path.stat().st_size}
        # Keep ALL technical author data for the gated resource viewer/download, not public catalog output.
        q.pop("prepared_hints", None)
        q["translations"] = {lang: {**q["translations"][lang], "reference_solution": texts[lang]["reference_solution"]}
                             for lang in ("he", "en")}
        q["website_editorial"] = {"solution_added": bool(edit.get("reference_solution")),
                                  "hints_translated": True, "human_review_pending": True}
        primary = PRIMARY[i]
        criteria = [
            ("correctness", .55, "Satisfies the specific question and constraints; compare against the proposed reference, accepting equivalent valid approaches.", "עונה נכון על השאלה והאילוצים; יש לקבל גם דרך תקפה אחרת מהפתרון המוצע."),
            ("reasoning", .30, "Explains the reasoning, assumptions and any efficiency claims with justification.", "מסביר את הדרך, ההנחות וטענות היעילות עם הצדקה."),
            ("verification", .15, "Checks relevant examples and edge cases; identifies ambiguity instead of silently inventing requirements.", "בודק דוגמאות ומקרי קצה ומציין עמימות בלי להמציא דרישות."),
        ]
        result.append({
            "key": "prep-" + q["key"], "version": q["version"], "status": "trial", "origin": "user_supplied",
            "format": "code" if q["category"] == "software" else "construct" if q["category"] == "hardware" else "explain",
            "practice_modes": ["quick", "deep"],
            "subject": skill_subject[primary],
            # Compatibility sentinel only: never displayed as calibrated difficulty, never scored as evidence.
            "difficulty": 5, "estimated_minutes": q.get("estimated_minutes"),
            "archetype": "coding" if q["category"] == "software" else "design" if q["category"] == "hardware" else "conceptual",
            "skills": [{"skill": primary, "weight": 1, "primary": True}],
            "rubric": [{"key": k, "weight": w, "description": {"en": en, "he": he}} for k, w, en, he in criteria],
            "translations": texts, "reuse_status": "pending_review", "exposure_risk": "high",
            "source_name": "Founder-supplied interview preparation archive", "reviewed_by": None,
            "review_notes": "Imported for founder pilot. Difficulty, technical review, rubric and reuse review pending. No mastery evidence or competitive XP.",
            "assets": {
                "titles": {lang: texts[lang]["title"] for lang in texts},
                "preparation_id": ident, "collection": "interview_preparation", "assessment_ready": False,
                "difficulty_status": "unrated", "source_difficulty": q["difficulty"],
                "category": "logic" if q["category"] == "logical_reasoning" else q["category"],
                "topics": q["topics"], "reported_companies": q["reported_companies"],
                "company_attribution_status": q["company_attribution_status"],
                "related_question_ids": q["related_question_ids"], "code_language": q.get("code_language"),
                "bank_media": media, "preparation_resource": q,
                "source_sha256": hashlib.sha256(json.dumps(original, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
            },
        })
    return result, uploads


def main():
    questions, uploads = load()
    (SEEDS / "questions/preparation_bank.json").write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (SEEDS / "preparation_uploads.json").write_text(json.dumps({"bucket": BUCKET, "files": uploads}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(questions)} questions and {len(uploads)} assets; original archive unchanged.")


if __name__ == "__main__":
    main()
