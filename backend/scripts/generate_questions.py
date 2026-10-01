"""Draft new bank questions with the model, in our exact seed format, for an engineer to review.

    uv run python scripts/generate_questions.py --dry-run                       # the plan: how many per skill, no calls
    uv run python scripts/generate_questions.py --skills boolean_algebra --per-skill 3   # a small real run
    uv run python scripts/generate_questions.py --per-skill 12 --verify         # the full bank: ~400 drafts, judged

What it does, per skill of the role (hardware) and of the software track:
  1. asks the drafting model for a batch of questions in the BankQuestion shape (both languages, rubric with
     weights, three hints, named common errors, an optional deterministic check with its own pass/fail answers),
     given the skill's proficiency rubric, the difficulty band and the titles that already exist;
  2. validates every draft the way the seed loader does (pydantic shape, skills and tips exist, the check accepts
     its own good answers and rejects its bad ones) and drops what fails, with the reason in the report;
  3. with --verify, has the judge grade the draft's own reference solution: a reference that does not band STRONG
     is kept but flagged `needs_attention`, because either the question or the reference is unclear;
  4. writes seeds/question_drafts/generated_bank.json (status in_review, origin generated, reuse pending_review) and a
     coverage report under docs/. The drafts folder sits OUTSIDE seeds/questions, which the loader reads, so nothing
     reaches the database unless someone moves a reviewed question into seeds/questions and runs the loader.

Nothing here touches the database. Shaked's decision of 2026-10-01: the drafts stay aside as an option.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.engine import catalog as catalog_module  # noqa: E402
from app.engine import evaluator, scores
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.checks import run_check  # noqa: E402
from app.engine.params import DEFAULT_PARAMS  # noqa: E402
from app.engine.providers import AnthropicProvider, LLMError, LLMRequest, call  # noqa: E402
from app.schemas.bank import BankQuestion  # noqa: E402

BACKEND = Path(__file__).resolve().parent.parent
SEEDS = BACKEND / "seeds"
OUTPUT = SEEDS / "question_drafts" / "generated_bank.json"   # outside seeds/questions on purpose: the loader must never pick drafts up by accident
REPORT = BACKEND.parent / "docs" / f"question-bank-{date.today().isoformat()}.md"

HARDWARE_SUBJECTS = ("digital_fundamentals", "sequential_logic", "fsms")
SOFTWARE_SUBJECTS = ("relevant_programming",)
SOFT_SUBJECTS = ("reasoning", "projects_behavioral")
FORMATS = ("truth_table", "short_answer", "explain", "construct", "hdl", "code", "waveform")
ARCHETYPES = ("conceptual", "design", "coding", "debugging")


# ---------------------------------------------------------------- what the model fills in (a flatter BankQuestion)
class DraftText(BaseModel):
    title: str = Field(description="4 to 8 words, names the task, no question mark")
    prompt: str = Field(description="the question as the interviewer says it: concrete, self-contained, every number given")
    requirements: str = Field(description="what a complete answer must contain, numbered (1) (2) (3)")
    reference_solution: str = Field(description="a full correct answer with every number, expression or code")
    hints: list[str] = Field(description="exactly three: level 1 an angle that reveals nothing, level 2 names the concept, level 3 the first concrete step")
    accepted_approaches: list[str] = Field(description="other valid ways to answer, 1 to 3 lines")


class DraftRubric(BaseModel):
    key: str = Field(description="snake_case")
    weight: float = Field(description="all weights sum to 1.0")
    en: str
    he: str


class DraftError(BaseModel):
    key: str = Field(description="snake_case, the same key in both languages' common_errors")
    core: bool = Field(description="true only when making this error means the central idea is not understood (at most one per question)")
    tip_key: str | None = Field(default=None, description="one of the coaching tip keys given, or null")
    explanation_en: str = Field(description="one sentence: what the candidate did and why it is wrong")
    explanation_he: str = Field(description="the same sentence in Hebrew")


class CodeCase(BaseModel):
    args_json: str = Field(description="the positional arguments as a JSON array, e.g. \"[180]\" or \"[[1,2,3], 2]\"")
    expected_json: str = Field(description="the expected return value as JSON, e.g. \"4\" or \"true\" or \"[1,2]\"")


class DraftCheck(BaseModel):
    type: str = Field(description="truth_table | numeric | code_tests")
    # truth_table
    variables: list[str] | None = Field(default=None, description="truth_table: input names, most significant first, up to 5")
    minterms: list[int] | None = Field(default=None, description="truth_table: the input rows (as unsigned numbers) whose output is 1")
    output_name: str | None = Field(default=None, description="truth_table: the output's name")
    # numeric
    expected: float | None = Field(default=None, description="numeric: the expected value in the given unit")
    unit: str | None = Field(default=None, description="numeric: the unit, e.g. ns, MHz, or an empty string")
    tolerance_abs: float | None = Field(default=None, description="numeric: absolute tolerance")
    tolerance_rel: float | None = Field(default=None, description="numeric: relative tolerance, e.g. 0.01, when no absolute one")
    output_names: list[str] | None = Field(default=None, description="numeric: names the candidate may call the quantity")
    # code_tests
    entry: list[str] | None = Field(default=None, description="code_tests: accepted function names")
    cases: list[CodeCase] | None = Field(default=None, description="code_tests: 4 to 8 cases including edge cases")
    pass_answers: list[str] = Field(description="2 to 4 answers a candidate might write that the check must accept")
    fail_answers: list[str] = Field(description="2 to 3 wrong answers the check must reject")

    def spec(self) -> dict:
        if self.type == "truth_table":
            return {"variables": self.variables or [], "minterms": self.minterms or [], "output_name": self.output_name or "F"}
        if self.type == "numeric":
            spec: dict = {"expected": self.expected, "unit": self.unit or "", "output_names": self.output_names or []}
            if self.tolerance_abs is not None:
                spec["tolerance_abs"] = self.tolerance_abs
            else:
                spec["tolerance_rel"] = self.tolerance_rel if self.tolerance_rel is not None else 0.01
            return spec
        if self.type == "code_tests":
            cases = []
            for c in self.cases or []:
                try:
                    cases.append({"args": json.loads(c.args_json), "expected": json.loads(c.expected_json)})
                except json.JSONDecodeError:
                    continue
            return {"language": "python", "timeout_ms": 5000, "entry": self.entry or [], "cases": cases}
        return {}


class SecondarySkill(BaseModel):
    skill: str
    weight: float


class DraftQuestion(BaseModel):
    slug: str = Field(description="kebab-case, 3 to 5 words, unique, describes the task")
    format: str = Field(description="one of " + ", ".join(FORMATS))
    archetype: str = Field(description="one of " + ", ".join(ARCHETYPES))
    difficulty: int = Field(description="1 to 10 within the band given")
    estimated_minutes: int = Field(description="4 to 25")
    practice_modes: list[str] = Field(description="subset of quick, deep, simulation; quick only when it takes 6 minutes or less")
    secondary_skills: list[SecondarySkill] = Field(default_factory=list, description="up to two from the catalog list; the primary skill gets the rest of the weight (all weights sum to 1.0)")
    rubric: list[DraftRubric] = Field(description="3 to 5 criteria")
    common_errors: list[DraftError] = Field(description="2 to 4 realistic mistakes")
    check: DraftCheck | None = Field(default=None, description="only when the answer can be checked mechanically; otherwise null")
    exposure_risk: str = Field(default="low", description="high if the question appears in every interview-prep resource, medium if common, else low")
    en: DraftText
    he: DraftText


class DraftBatch(BaseModel):
    questions: list[DraftQuestion]


SYSTEM = """You write interview questions for JobRun, a Hebrew-first practice platform for students and junior engineers
interviewing for digital hardware and adjacent software roles in Israel (Intel, Nvidia, Apple, Mobileye, Marvell,
start-ups). You are a senior engineer who has run hundreds of these interviews.

Rules, all of them binding:
- Original questions in your own words. Never reproduce a question from a book, a website or a course. Ideas are
  fine (a majority vote, a sequence detector); wording and specific setups are yours. Never attribute a question
  to a company.
- Every question is self-contained: every number, signal name, width, clock, constraint and function signature
  the candidate needs is in the prompt. No "assume a typical" anything.
- The reference solution is complete and correct, with every intermediate number or the full code. Check your own
  arithmetic twice; a wrong reference is the worst outcome.
- Both languages say exactly the same thing. Hebrew as Israeli engineers speak it: technical terms in English
  letters where that is what people say (MUX, setup, hold, flip-flop, reset, enable, overflow, FSM, Verilog),
  Hebrew for everything else, no transliteration of words that have a Hebrew term (מונה, אוגר, שער, מצב).
  Address the reader in the plural (אתם).
- Rubric: 3 to 5 criteria that a grader can decide from the answer alone, weights summing to 1.0, both languages.
- Hints: level 1 gives an angle and reveals nothing; level 2 names the concept; level 3 gives the first concrete
  step but not the answer.
- Common errors: 2 to 4 mistakes candidates actually make on this task, each with a snake_case key and one
  sentence per language explaining what was done and why it is wrong. Mark at most one as core.
- Deterministic check only when a machine can decide it: a truth_table for a Boolean function of up to 5 inputs
  (minterms are the input rows, read as an unsigned number with the first variable as the most significant bit,
  whose output is 1), a numeric check for a single number with a unit and a tolerance, or code_tests for a Python
  function with 4 to 8 cases including edge cases. Give 2 to 4 answers the check must accept, written the way
  candidates write (an expression, a sentence with the number, a fenced python block), and 2 to 3 it must reject.
  Otherwise set check to null.
  Spec formats, exactly as our loader reads them:
    truth_table: {"variables": ["A","B","C"], "minterms": [3,5,6,7], "output_name": "alarm"}
    numeric:     {"expected": 1.4, "unit": "ns", "tolerance_abs": 0.01, "output_names": ["Tmin", "minimum period"]}
    code_tests:  {"language": "python", "timeout_ms": 5000, "entry": ["count_set_bits", "popcount"], "cases": [{"args": [180], "expected": 4}, {"args": [0], "expected": 0}]}
  A truth_table pass answer is a Boolean expression over the variables (AB + AC, (A & B) | C, A'B, ~A & B); a
  numeric pass answer is a sentence or equation that contains the number with its unit; a code_tests pass answer
  is a fenced python block defining one of the entry names.
- Difficulty is within the band given; spread the batch across it; vary the format and the archetype.
- Do not repeat any of the existing titles listed, nor each other.
Reply only with the JSON the schema asks for."""


def user_prompt(skill, subject_label: str, existing_titles: list[str], count: int, band: tuple[int, int], tip_keys: list[str],
                catalog_skills: list[str], track: str) -> str:
    rubric = "\n".join(f"  level {k}: {v}" for k, v in sorted(skill.proficiency_rubric.items()))
    titles = "\n".join(f"  - {t}" for t in existing_titles) or "  (none yet)"
    return (
        f"Skill: {skill.key} — {skill.label}\nSubject: {subject_label}\nTrack: {track}\n"
        f"Skill description: {skill.description or '(none)'}\n"
        f"What each proficiency level looks like:\n{rubric}\n"
        f"Difficulty band for this batch: {band[0]} to {band[1]} (1 = first-year exercise, 10 = senior design review).\n"
        f"Write {count} questions. Their primary skill is {skill.key}; secondary skills may come only from: "
        f"{', '.join(catalog_skills)}.\n"
        f"Coaching tip keys you may reference: {', '.join(tip_keys)}.\n"
        f"Titles that already exist for this skill (do not repeat them or their setups):\n{titles}\n"
        f"Formats available: {', '.join(FORMATS)}. Archetypes: {', '.join(ARCHETYPES)}."
    )


def to_bank(draft: DraftQuestion, skill_key: str, subject: str, track: str) -> dict:
    """The seed-file shape the loader reads, from the flatter draft."""
    secondary = [s for s in draft.secondary_skills if s.skill and s.skill != skill_key]
    secondary_weight = sum(float(s.weight) for s in secondary)
    primary_weight = round(max(0.4, 1.0 - secondary_weight), 3)
    weights = [{"skill": skill_key, "weight": primary_weight, "primary": True}]
    scale = (1.0 - primary_weight) / secondary_weight if secondary and secondary_weight > 0 else 0
    for s in secondary:
        weights.append({"skill": s.skill, "weight": round(float(s.weight) * scale, 3)})
    rubric_total = sum(r.weight for r in draft.rubric) or 1.0
    rubric = [{"key": r.key, "weight": round(r.weight / rubric_total, 3), "description": {"en": r.en, "he": r.he}} for r in draft.rubric]
    # rounding can leave the sum a hair off; give the difference to the heaviest criterion
    drift = round(1.0 - sum(r["weight"] for r in rubric), 3)
    if rubric and abs(drift) > 0:
        heaviest = max(rubric, key=lambda r: r["weight"])
        heaviest["weight"] = round(heaviest["weight"] + drift, 3)
    errors = [{"key": e.key, "core": bool(e.core), "skill": skill_key, **({"tip_key": e.tip_key} if e.tip_key else {})} for e in draft.common_errors]
    key = f"gen-{skill_key.replace('_', '-')}-{re.sub(r'[^a-z0-9-]', '-', draft.slug.lower()).strip('-')}"
    question = {
        "key": key,
        "version": 1,
        "status": "in_review",
        "origin": "generated",
        "format": draft.format if draft.format in FORMATS else "explain",
        "practice_modes": [m for m in draft.practice_modes if m in ("quick", "deep", "simulation")] or ["deep"],
        "subject": subject,
        "difficulty": max(1, min(10, int(draft.difficulty))),
        "estimated_minutes": max(3, min(30, int(draft.estimated_minutes))),
        "archetype": draft.archetype if draft.archetype in ARCHETYPES else "conceptual",
        "skills": weights,
        "rubric": rubric,
        "common_errors": errors,
        "deterministic_check": {"type": draft.check.type, "spec": draft.check.spec()} if draft.check and draft.check.type in ("truth_table", "numeric", "code_tests") else None,
        "check_self_test": {"pass": draft.check.pass_answers, "fail": draft.check.fail_answers} if draft.check and draft.check.type in ("truth_table", "numeric", "code_tests") else None,
        "assets": {
            "collection": "jobrun_generated_v1",
            "category": "hardware" if track == "hardware" else "software",
            "titles": {"he": draft.he.title, "en": draft.en.title},
            "shared_code": None,
            "code_language": "python" if draft.check and draft.check.type == "code_tests" else None,
        },
        "source_name": "JobRun original (model draft, generate_questions.py)",
        "source_url": None,
        "license": "original",
        "reuse_status": "pending_review",
        "review_notes": f"Drafted by the model on {date.today().isoformat()} for skill {skill_key}. Needs technical review, rubric review and Hebrew/English parity review before publishing.",
        "exposure_risk": draft.exposure_risk if draft.exposure_risk in ("low", "medium", "high") else "low",
        "translations": {},
    }
    for lang, text in (("en", draft.en), ("he", draft.he)):
        question["translations"][lang] = {
            "title": text.title,
            "prompt": text.prompt,
            "requirements": text.requirements,
            "reference_solution": text.reference_solution,
            "hints": list(text.hints)[:3],
            "common_errors": {e.key: (e.explanation_en if lang == "en" else e.explanation_he) for e in draft.common_errors},
            "accepted_approaches": list(text.accepted_approaches),
            "parity_checked": False,
        }
    return question


def validate(question: dict, cat) -> list[str]:
    """The loader's own rules, on one draft: the pydantic shape, skills and tips exist, the check passes its self-test."""
    try:
        model = BankQuestion.model_validate(question)
    except ValidationError as exc:
        return [f"shape: {str(exc).splitlines()[0]}"]
    problems = []
    if model.subject not in cat.domains:
        problems.append(f"subject {model.subject!r} unknown")
    for link in model.skills:
        if link.skill not in cat.leaf_skills:
            problems.append(f"skill {link.skill!r} unknown")
    for error in model.common_errors:
        if error.tip_key and error.tip_key not in cat.tips:
            problems.append(f"tip {error.tip_key!r} unknown")
    for lang in ("en", "he"):
        text = model.translations[lang]
        if any(not h.strip() for h in text.hints):
            problems.append(f"{lang}: empty hint")
        if any(not v.strip() for v in text.common_errors.values()):
            problems.append(f"{lang}: empty common-error explanation")
        if len(text.prompt) < 60:
            problems.append(f"{lang}: prompt too short to be self-contained")
    problems.extend(catalog_module._self_test(model))
    return problems


async def draft_batch(provider, skill, subject_label, existing, count, band, tip_keys, catalog_skills, track, model):
    request = LLMRequest(role="generator",
                         system=[SYSTEM],
                         user=user_prompt(skill, subject_label, existing, count, band, tip_keys, catalog_skills, track),
                         schema=DraftBatch, prompt_version="gen-1", effort="high", max_tokens=16000)
    response = await call(provider, request, timeout_seconds=600)
    return response


async def verify_reference(provider, question: BankQuestion, cat) -> tuple[str, str]:
    """The judge grades the draft's own English reference. Returns (band, summary)."""
    skill = cat.leaf_skills[question.primary_skill]
    answer = question.translations["en"].reference_solution
    check = run_check(question.deterministic_check, answer, sandbox=False) if question.deterministic_check else None
    result = await evaluator.evaluate(provider, question_context=evaluator.question_block(question, "en", skill),
                                      known_error_keys={e.key for e in question.common_errors}, language="en",
                                      difficulty=question.difficulty, answer=answer, check=check, glossary=cat.glossary)
    if not result.ok:
        return "FAILED", ",".join(result.flags)
    ev = scores.apply_check_result(result.evaluation, check, DEFAULT_PARAMS)
    core = bool(set(ev.misconceptions) & question.core_misconception_keys)
    band = scores.classify_band(ev, core, DEFAULT_PARAMS)
    return band.value, ev.one_line_summary


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-skill", type=int, default=12, help="target questions per skill, existing ones included")
    parser.add_argument("--batch", type=int, default=2, help="questions per model call (2 keeps replies short enough to avoid read timeouts)")
    parser.add_argument("--skills", nargs="*", help="only these skill keys")
    parser.add_argument("--track", choices=["hardware", "software", "soft", "all", "hardware+software"], default="hardware+software",
                        help="hardware, software, soft (reasoning and behavioural) or all; default hardware and software")
    parser.add_argument("--model", default="claude-opus-5-5", help="the drafting model")
    parser.add_argument("--judge", default=None, help="the verifying judge; default: the configured judge")
    parser.add_argument("--verify", action="store_true", help="grade every draft's reference with the judge")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true", help="print the plan and exit")
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--append", action="store_true", help="keep what --out already holds and add to it")
    args = parser.parse_args()

    cat = load_catalog(SEEDS)
    role = next(iter(cat.roles.values()))
    role_skills = [row.skill for row in role.skill_set]
    tracks = {"hardware": HARDWARE_SUBJECTS, "software": SOFTWARE_SUBJECTS, "soft": SOFT_SUBJECTS}
    chosen = {"all": set(tracks), "hardware+software": {"hardware", "software"}}.get(args.track, {args.track})
    wanted_subjects = set(sum((list(v) for k, v in tracks.items() if k in chosen), []))
    # every leaf skill of the wanted subjects: the role's skills first, then the track's other skills (the software
    # skills sit outside the hardware role's skill set but are what the software track needs)
    ordered = list(dict.fromkeys([*role_skills, *sorted(cat.leaf_skills)]))
    skills = [cat.leaf_skills[k] for k in ordered if cat.leaf_skills[k].subject in wanted_subjects]
    if args.skills:
        skills = [cat.leaf_skills[k] for k in args.skills]
    existing = defaultdict(list)
    for q in cat.questions.values():
        existing[q.primary_skill].append(q.translations["en"].title if "en" in q.translations else q.key)
    previous: list[dict] = []
    if args.append and args.out.exists():
        previous = json.loads(args.out.read_text(encoding="utf-8"))
        for q in previous:
            existing[next(s["skill"] for s in q["skills"] if s.get("primary"))].append(q["translations"]["en"]["title"])

    plan = []
    for skill in skills:
        need = max(0, args.per_skill - len(existing[skill.key]))
        if need:
            plan.append((skill, need))
    total = sum(n for _, n in plan)
    calls = sum(-(-n // args.batch) for _, n in plan)
    print(f"{len(plan)} skills need questions; {total} drafts in about {calls} calls to {args.model}"
          + (f", then {total} judge calls" if args.verify else ""), flush=True)
    for skill, need in plan:
        print(f"  {skill.key:<28} have {len(existing[skill.key]):>2}  need {need:>2}  band {skill.min_difficulty}-{skill.max_difficulty}")
    if args.dry_run or not plan:
        return 0

    settings = get_settings()
    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY is not set", file=sys.stderr)
        return 2
    drafter = AnthropicProvider(api_key=settings.anthropic_api_key, model=args.model, role_models={"generator": args.model})
    judge = AnthropicProvider(api_key=settings.anthropic_api_key, model=args.judge or settings.anthropic_model, role_models={})
    tip_keys = sorted(cat.tips)
    catalog_skills = sorted(k for k, s in cat.leaf_skills.items() if s.subject in wanted_subjects or s.subject in HARDWARE_SUBJECTS + SOFTWARE_SUBJECTS)
    subject_label = {k: s.label for k, s in cat.skills.items()}
    semaphore = asyncio.Semaphore(args.concurrency)
    accepted: list[dict] = list(previous)
    rejected: list[tuple[str, str]] = []
    rejected_drafts: list[dict] = []
    flagged: list[tuple[str, str, str]] = []
    cost = 0.0
    started = time.perf_counter()

    def save(rows: list[dict]) -> None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    async def one_batch(skill, count, band, batch_index):
        nonlocal cost
        track = "hardware" if skill.subject in HARDWARE_SUBJECTS else "software" if skill.subject in SOFTWARE_SUBJECTS else "soft"
        async with semaphore:
            response = None
            for attempt in range(4):
                try:
                    response = await draft_batch(drafter, skill, subject_label.get(skill.subject, skill.subject), existing[skill.key],
                                                 count, band, tip_keys, catalog_skills, track, args.model)
                    break
                except LLMError as exc:
                    if attempt == 3 or not exc.retryable:
                        rejected.append((f"{skill.key} batch {batch_index}", f"model call failed: {exc}"))
                        return
                    await asyncio.sleep(8 * (attempt + 1))
                except Exception as exc:  # noqa: BLE001 - a read timeout or a parse error must not kill the run
                    if attempt == 3:
                        rejected.append((f"{skill.key} batch {batch_index}", f"model call failed: {type(exc).__name__}: {exc}"))
                        return
                    print(f"  ~ {skill.key} batch {batch_index}: {type(exc).__name__}, retrying", flush=True)
                    await asyncio.sleep(8 * (attempt + 1))
            if response is None or response.parsed is None:
                rejected.append((f"{skill.key} batch {batch_index}", "no structured reply"))
                return
        cost += response.usage.cost_usd(response.model) or 0.0
        batch: DraftBatch = response.parsed  # type: ignore[assignment]
        for draft in batch.questions:
            question = to_bank(draft, skill.key, skill.subject, track)
            problems = validate(question, cat)
            title = question["translations"]["en"]["title"]
            if title.lower() in {t.lower() for t in existing[skill.key]}:
                problems.append("duplicate title")
            if problems:
                rejected.append((question["key"], "; ".join(problems)))
                rejected_drafts.append(question)
                continue
            existing[skill.key].append(title)
            accepted.append(question)
            print(f"  + {question['key']}  d{question['difficulty']}  {title}", flush=True)
        save(accepted)

    jobs = []
    for skill, need in plan:
        low, high = skill.min_difficulty, skill.max_difficulty
        # a spread of bands across the batches so the skill gets easy and hard questions
        batches = -(-need // args.batch)
        for b in range(batches):
            count = min(args.batch, need - b * args.batch)
            span = max(1, high - low)
            band_low = low + (span * b) // max(1, batches)
            band_high = min(high, band_low + max(2, span // max(1, batches)))
            jobs.append(one_batch(skill, count, (band_low, band_high), b + 1))
    await asyncio.gather(*jobs)
    drafting_seconds = time.perf_counter() - started

    if args.verify:
        print(f"verifying {len(accepted) - len(previous)} references with {judge.model}…", flush=True)

        async def one_verify(question: dict):
            nonlocal cost
            async with semaphore:
                model = BankQuestion.model_validate(question)
                try:
                    band, summary = await verify_reference(judge, model, cat)
                except Exception as exc:  # noqa: BLE001
                    band, summary = "FAILED", f"{type(exc).__name__}: {exc}"
            if band != "STRONG":
                question["review_notes"] += f" needs_attention: the judge banded the reference {band} ({summary[:160]})."
                flagged.append((question["key"], band, summary[:160]))

        await asyncio.gather(*(one_verify(q) for q in accepted[len(previous):]))
        save(accepted)

    try:
        out_label = args.out.resolve().relative_to(BACKEND.parent).as_posix()
    except ValueError:
        out_label = str(args.out)
    for key, why in rejected:
        print(f"  - rejected {key}: {why}")
    if rejected_drafts:
        args.out.with_suffix(".rejected.json").write_text(json.dumps(rejected_drafts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(accepted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elapsed = time.perf_counter() - started
    new = accepted[len(previous):]
    by_skill = Counter(next(s["skill"] for s in q["skills"] if s.get("primary")) for q in new)
    with_check = sum(1 for q in new if q.get("deterministic_check"))
    lines = [
        f"# Question bank drafts — {date.today().isoformat()}",
        "",
        f"`scripts/generate_questions.py` drafted **{len(new)} questions** ({len(rejected)} drafts rejected by the loader's own rules)"
        f" for {len(by_skill)} skills with {args.model}, in {drafting_seconds / 60:.1f} min of drafting"
        + (f" and {(elapsed - drafting_seconds) / 60:.1f} min of judging with {judge.model}" if args.verify else "")
        + f", about ${cost:.2f}. Written to `{out_label}`, status `in_review`, nothing loaded.",
        "",
        f"- With a deterministic check: {with_check}",
        f"- Flagged `needs_attention` (the judge did not band the reference STRONG): {len(flagged)}" if args.verify else "- Not judged (run with --verify)",
        "",
        "## Coverage per skill (existing + new)",
        "",
        "| Skill | Existing | New | Rejected |",
        "|---|---:|---:|---:|",
    ]
    rejected_by_skill = Counter(k.split(" batch")[0] if " batch" in k else "-".join(k.split("-")[1:-3]) for k, _ in rejected)
    for skill, _need in plan:
        prior = len([t for t in existing[skill.key]]) - by_skill.get(skill.key, 0)
        lines.append(f"| {skill.label} | {prior} | {by_skill.get(skill.key, 0)} | {rejected_by_skill.get(skill.key.replace('_', '-'), 0) + rejected_by_skill.get(skill.key, 0)} |")
    if flagged:
        lines += ["", "## Needs attention (judge did not band the reference STRONG)", ""]
        lines += [f"- `{k}`: {band}. {summary}" for k, band, summary in flagged]
    if rejected:
        lines += ["", "## Rejected drafts and why", ""]
        lines += [f"- `{k}`: {why}" for k, why in rejected]
    lines += ["", "## Three samples", ""]
    for q in new[:3]:
        t = q["translations"]
        lines += [f"### {t['he']['title']} / {t['en']['title']} (d{q['difficulty']}, {q['format']}, {q['estimated_minutes']} min)", "",
                  t["he"]["prompt"], "", t["en"]["prompt"], "", f"Reference (en): {t['en']['reference_solution'][:600]}", ""]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{len(new)} accepted, {len(rejected)} rejected, {len(flagged)} flagged; ${cost:.2f}; {elapsed / 60:.1f} min. Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
