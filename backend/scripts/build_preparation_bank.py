"""Compile the founders' preparation archive without modifying a single source file.

Run from any directory. Produces an engine seed and a content-addressed upload manifest.
Original content lives in interview_preparation; editorial additions live beside this script's inputs.
Uncalibrated questions are study-only: feedback is provisional and does not earn skill evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.engine.solution_review import attach_registered_reviews  # noqa: E402

BANK = ROOT / "interview_preparation"
SEEDS = ROOT / "backend/seeds"
BUCKET = "question-bank-media"
MATERIAL_FIELDS = frozenset({
    "assumptions", "optimality", "verification", "edge_cases", "interview_answer", "common_mistakes",
    "solution_extensions", "prompt_variants", "transition_tables", "truth_table", "waveform_observations",
    "fsm", "strategy", "source_ambiguities", "ambiguities", "solution_networks", "area_optimization",
    "technical_references", "component_truth_table", "circuit_interpretation", "network", "diagnostic_test",
    "answer_branches", "netlist", "netlists", "component_delays_ns", "retiming_alternative", "course_terminology",
    "terminology_clarification", "alternative_solution_notes", "descending_diagram_extension",
    "diagram_description", "driver_explanation_he", "eight_cell_alternative", "formula_interpretation",
    "group_logic_derivation_he", "group_logic_derivation_verification", "hierarchy_diagram_explanation_he",
    "n2_design_comparison", "original_formula_latex", "parallel_products_explanation", "part_5_cost_model",
    "part_6_two_level_explanation", "recursive_two_bit_alternative", "relationship_note", "solution_references",
    "solution_schematic_verification", "solution_gate_schematic_verification", "editorial_notes",
})

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
    "basic_data_structures", "estimation_sanity_checks",
    "estimation_sanity_checks", "arrays_and_search", "arrays_and_search", "edge_detection", "fsm_state_tables",
    "registers_shifters", "fsm_state_tables", "estimation_sanity_checks", "boolean_algebra", "counters",
    "estimation_sanity_checks",
    "fsm_state_tables", "combinational_blocks", "combinational_blocks", "fsm_state_tables", "estimation_sanity_checks", "latches_flip_flops", "estimation_sanity_checks", "binary_arithmetic", "estimation_sanity_checks",
    "estimation_sanity_checks", "basic_data_structures", "estimation_sanity_checks", "estimation_sanity_checks", "counters",
    "latches_flip_flops", "arrays_and_search", "registers_shifters", "bit_manipulation",
    "debugging_methodology", "combinational_blocks", "estimation_sanity_checks", "arrays_and_search", "estimation_sanity_checks",
    "latches_flip_flops", "registers_shifters", "debugging_methodology", "bit_manipulation", "counters",
    "estimation_sanity_checks", "arrays_and_search", "debugging_methodology", "estimation_sanity_checks",
    "latches_flip_flops", "estimation_sanity_checks", "estimation_sanity_checks",
    "combinational_blocks", "arrays_and_search", "bit_manipulation",
    "arrays_and_search", "estimation_sanity_checks", "edge_detection", "boolean_algebra",
    "estimation_sanity_checks", "bit_manipulation", "debugging_methodology", "estimation_sanity_checks",
    "arrays_and_search", "arrays_and_search", "debugging_methodology", "binary_arithmetic", "arrays_and_search", "basic_data_structures", "latches_flip_flops", "setup_hold_timing", "bit_manipulation",
    "latches_flip_flops", "combinational_blocks", "arrays_and_search", "combinational_blocks", "combinational_blocks", "bit_manipulation", "combinational_blocks", "estimation_sanity_checks", "estimation_sanity_checks",
    "estimation_sanity_checks", "arrays_and_search", "basic_data_structures", "debugging_methodology", "binary_arithmetic", "combinational_blocks",
    "estimation_sanity_checks", "binary_arithmetic", "basic_data_structures", "estimation_sanity_checks", "arrays_and_search",
    "estimation_sanity_checks", "estimation_sanity_checks", "fsm_sequence_detectors", "estimation_sanity_checks", "combinational_blocks", "basic_data_structures", "combinational_blocks", "debugging_methodology", "binary_arithmetic", "arrays_and_search", "binary_arithmetic",
    "arrays_and_search", "bit_manipulation", "fsm_state_tables", "binary_arithmetic", "basic_data_structures", "arrays_and_search", "estimation_sanity_checks", "estimation_sanity_checks", "combinational_blocks", "estimation_sanity_checks", "registers_shifters",
    "basic_data_structures", "arrays_and_search", "arrays_and_search", "bit_manipulation", "counters", "combinational_blocks", "debugging_methodology", "boolean_algebra", "estimation_sanity_checks", "combinational_blocks", "estimation_sanity_checks", "debugging_methodology",
    "arrays_and_search", "fsm_controllers", "basic_data_structures", "arrays_and_search", "estimation_sanity_checks", "estimation_sanity_checks", "estimation_sanity_checks", "estimation_sanity_checks", "estimation_sanity_checks", "estimation_sanity_checks", "estimation_sanity_checks", "fsm_state_tables", "boolean_algebra", "fsm_sequence_detectors", "binary_arithmetic", "setup_hold_timing", "setup_hold_timing", "setup_hold_timing",
    "debugging_methodology", "binary_arithmetic", "binary_arithmetic", "binary_arithmetic", "arrays_and_search", "estimation_sanity_checks", "arrays_and_search", "arrays_and_search", "estimation_sanity_checks", "arrays_and_search",
    "arrays_and_search", "basic_data_structures", "estimation_sanity_checks", "registers_shifters", "estimation_sanity_checks", "edge_detection", "basic_data_structures", "estimation_sanity_checks", "arrays_and_search", "number_representation", "estimation_sanity_checks",
    "combinational_blocks", "combinational_blocks", "estimation_sanity_checks", "counters", "estimation_sanity_checks", "fsm_sequence_detectors", "boolean_algebra", "binary_arithmetic", "fsm_sequence_detectors", "fsm_controllers", "estimation_sanity_checks",
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
        yield from re.findall(r"(?:sources|diagrams|solutions)/[\w./-]+\.(?:png|sv|py|cpp|java|asm|c)\b", value)
    elif isinstance(value, dict):
        for v in value.values():
            yield from paths_in(v)
    elif isinstance(value, list):
        for v in value:
            yield from paths_in(v)


def learner_text(edit, ident):
    """Apply paired website copy without granting approval or editing archived source text."""
    overrides = edit.get("learner_text", {})
    if not isinstance(overrides, dict) or (overrides and set(overrides) != {"he", "en"}):
        raise ValueError(f"{ident}: learner text edits must include Hebrew and English")
    for replacement in overrides.values():
        if not isinstance(replacement, dict) or set(replacement) - {"title", "prompt", "reference_solution"}:
            raise ValueError(f"{ident}: unsupported learner text field")
        if any(not isinstance(v, str) or not v.strip() for v in replacement.values()):
            raise ValueError(f"{ident}: learner text must contain nonempty strings")
    if overrides and set(overrides["he"]) != set(overrides["en"]):
        raise ValueError(f"{ident}: edit the same learner text fields in both languages")
    return overrides


def load_material_localizations():
    result = {}
    for path in sorted((SEEDS / "preparation_localization").glob("*.json")):
        chunk = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(chunk, dict) or result.keys() & chunk.keys():
            raise ValueError(f"Invalid or duplicate material localization in {path.name}")
        result.update(chunk)
    return result


def learner_material(question, localizations):
    ident = question["id"]
    paired = localizations.get(ident)
    expected = {key for key in MATERIAL_FIELDS if question.get(key) not in (None, "", [], {})}
    if not isinstance(paired, dict) or set(paired) != expected:
        raise ValueError(f"{ident}: technical translations must cover exactly {sorted(expected)}")
    for key, values in paired.items():
        if not isinstance(values, dict) or set(values) != {"he", "en"}:
            raise ValueError(f"{ident}.{key}: both technical material languages are required")
        if any(values[lang] in (None, "", [], {}) for lang in ("he", "en")):
            raise ValueError(f"{ident}.{key}: technical translations must not be empty")
    return paired


def load():
    source = json.loads((BANK / "questions.json").read_text(encoding="utf-8-sig"))
    additions = json.loads((SEEDS / "preparation_editorial.json").read_text(encoding="utf-8"))
    localizations = load_material_localizations()
    if set(localizations) != {q["id"] for q in source["questions"]}:
        raise ValueError("Technical translations must cover the complete preparation archive")
    if len(PRIMARY) != len(source["questions"]):
        raise ValueError("Primary skill mapping must cover the complete preparation archive")
    skill_subject = {}
    for p in (SEEDS / "skills").glob("*.json"):
        for skill in json.loads(p.read_text(encoding="utf-8")):
            skill_subject[skill["key"]] = skill.get("parent")
    result, uploads = [], {}
    for i, original in enumerate(source["questions"]):
        q = strip_personal(original)
        ident = q["id"]
        edit = additions[ident]
        overrides = learner_text(edit, ident)
        texts = {}
        for lang in ("he", "en"):
            replacement = overrides.get(lang, {})
            text = {**q["translations"][lang], **replacement}
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
        # Authored question geometry may be needed before solving. This explicit
        # marker never makes a raw source screenshot available to learners.
        prompt_diagrams = {m["path"] for m in q.get("media_assets", [])
                           if m.get("type") == "prompt_diagram" and m.get("path")}
        if any(not p.startswith("diagrams/") or not p.endswith(".png") for p in prompt_diagrams):
            raise ValueError(f"{ident}: prompt diagrams must be authored PNGs in diagrams/")
        refs = {p for p in paths_in(q) if p.endswith('.png')}
        for field in ("solution_code_path", "solution_code_paths", "alternative_solution_code_path", "solution_model_path"):
            refs.update(paths_in(q.get(field)))
        # Include every preserved illustration for this question, including older alternatives.
        refs |= {str(p.relative_to(BANK)).replace("\\", "/")
                 for folder in ("sources", "diagrams") for p in (BANK / folder).glob(ident.lower() + "*")
                 if p.suffix == ".png"}
        descriptions = {m["path"]: m.get("description", "") for m in q.get("media_assets", []) if m.get("path")}
        media_languages = {m["path"]: m["language"] for m in q.get("media_assets", []) if m.get("language")}
        if any(language not in ("he", "en") for language in media_languages.values()):
            raise ValueError(f"{ident}: unsupported illustration language")
        for n, relative in enumerate(sorted(refs)):
            path = (BANK / relative).resolve()
            if not path.is_relative_to(BANK.resolve()) or not path.is_file():
                raise ValueError(f"{ident}: missing/unsafe asset {relative}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            storage_path = f"{ident.lower()}/{digest[:20]}-{path.name}"
            is_prompt = relative in source_paths or relative in prompt_diagrams
            media.append({"id": f"asset-{n + 1}", "path": storage_path, "filename": path.name,
                          "kind": "image" if path.suffix == ".png" else "file",
                          "role": "prompt" if is_prompt else "solution",
                          "caption": descriptions.get(relative, ""), "source_path": relative,
                          "sha256": digest})
            if relative in media_languages:
                media[-1]["language"] = media_languages[relative]
            uploads[storage_path] = {"local_path": relative, "sha256": digest, "bytes": path.stat().st_size}
        # Keep ALL technical author data for the gated resource viewer/download, not public catalog output.
        q.pop("prepared_hints", None)
        q["translations"] = {lang: {**q["translations"][lang], **overrides.get(lang, {}),
                                    "reference_solution": texts[lang]["reference_solution"]}
                             for lang in ("he", "en")}
        # Keep the archive's author data intact. Only the learner-facing view is
        # translated; source records, proofs, code and review status stay available.
        q["learner_material"] = learner_material(q, localizations)
        q["website_editorial"] = {"solution_added": bool(edit.get("reference_solution")),
                                  "hints_translated": True, "human_review_pending": True,
                                  "learner_text_edited": bool(overrides)}
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
    registry = json.loads((SEEDS / "solution_review_attestations.json").read_text(encoding="utf-8"))
    attach_registered_reviews(result, registry)
    return result, uploads


def main():
    questions, uploads = load()
    (SEEDS / "questions/preparation_bank.json").write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (SEEDS / "preparation_uploads.json").write_text(json.dumps({"bucket": BUCKET, "files": uploads}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(questions)} questions and {len(uploads)} assets; original archive unchanged.")


if __name__ == "__main__":
    main()
