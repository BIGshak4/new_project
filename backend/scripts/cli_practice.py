"""Deep practice in the terminal: the whole coaching loop without a web UI.

    uv run python scripts/cli_practice.py                     # manual provider, English
    uv run python scripts/cli_practice.py --language he
    uv run python scripts/cli_practice.py --provider anthropic
    uv run python scripts/cli_practice.py --question majority_vote_three_sensors --debug

While answering:   :hint   next hint level      :reveal   show the reference (no evidence if before submit)
                   :skip   another question     :quit     stop
Finish a multi-line answer with a line containing only a dot.

With the manual provider every model call is written to workdir/manual_llm/ as
NNN_<role>.request.md, and the loop waits for NNN_<role>.response.json (or .md).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.engine import bank, plan_router, scores  # noqa: E402
from app.engine.catalog import Catalog, CatalogError, load_catalog  # noqa: E402
from app.engine.plan import merge_skill_sets  # noqa: E402
from app.engine.practice import PracticeAttempt, PracticeContext, PracticeOutcome  # noqa: E402
from app.engine.providers import build_provider  # noqa: E402
from app.schemas.engine import PlanSkill  # noqa: E402
from app.services.local_store import LocalStore  # noqa: E402

RULE = "-" * 78
LABELS = {
    "en": {"what": "What happened", "why": "Why it matters", "next": "What to practice next",
           "compare": "Your reasoning vs the reference", "tip": "Tip", "follow": "Follow-up question",
           "confidence": "Before you answer: how confident are you, 1 (low) to 5 (high)? ",
           "answer": "Your answer (end with a single '.' on its own line):", "level": "level", "provisional": "provisional",
           "why_this": "Why this question", "done": "Attempt saved."},
    "he": {"what": "מה קרה", "why": "למה זה חשוב", "next": "מה לתרגל הלאה",
           "compare": "הדרך שלכם מול הפתרון המוצע", "tip": "טיפ", "follow": "שאלת המשך",
           "confidence": "לפני שעונים: כמה אתם בטוחים, מ-1 (נמוך) עד 5 (גבוה)? ",
           "answer": "התשובה שלכם (סיימו בשורה שמכילה רק נקודה):", "level": "רמה", "provisional": "זמנית",
           "why_this": "למה השאלה הזו", "done": "הניסיון נשמר."},
}


def read_answer(prompt: str) -> str:
    print(prompt)
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == ".":
            break
        if line.strip().startswith(":") and not lines:
            return line.strip()
        lines.append(line)
    return "\n".join(lines).strip()


def build_plan(catalog: Catalog, role_slug: str, company_slug: str, seniority: str) -> list[PlanSkill]:
    role, company = catalog.roles[role_slug], catalog.companies[company_slug]
    return merge_skill_sets(role_rows=role.skill_set, company_rows=company.skill_set, focus_skill_keys=[],
                            company_weight_share=company.company_weight_share, seniority=seniority,
                            planned_duration_min=45, catalog=catalog.leaf_skills)


def pick_question(catalog: Catalog, plan: list[PlanSkill], store: LocalStore, args, difficulty_ceiling: int):
    questions = list(catalog.questions.values())
    if args.question:
        return catalog.questions[args.question], "new", None
    required = {s.key: s.required_level for s in plan}
    coverage = bank.coverage_by_skill(questions, language=args.language, allow_in_review=True, require_parity=False)
    activity = plan_router.next_activity(
        plan=plan, profile=store.profile(required), today=date.today(), recent=store.recent_activities(),
        minutes_available_today=args.minutes, bank_coverage=coverage, diagnostic_done=True)
    ordered = [activity] if activity else []
    # fall back through every skill the bank covers, heaviest first
    ordered += [plan_router.Activity("deep", [s.key], 20, reason_code="unassessed", reason_facts={"skill": s.key})
                for s in sorted(plan, key=lambda s: -s.combined_weight) if s.key in coverage]
    for candidate in ordered:
        for skill in candidate.skills:
            state = store.skill_states().get(skill)
            level = state.provisional_level if state and state.provisional_level else required.get(skill, 2)
            target = min(difficulty_ceiling, scores.min_difficulty_for_level(level) + 1)
            mode = candidate.mode if candidate.mode in ("quick", "deep") else "deep"
            for try_mode in (mode, "deep", "quick"):
                selection = bank.select_question(questions, skill=skill, difficulty=target, mode=try_mode,
                                                 language=args.language, seen_keys=store.seen_questions,
                                                 allow_in_review=True, require_parity=False, difficulty_window=9)
                if selection:
                    reason = plan_router.reason_text(candidate, args.language, catalog.skill_labels())
                    return selection.question, selection.familiarity, reason
    return None, None, None


def show_outcome(outcome: PracticeOutcome, labels: dict, debug: bool) -> None:
    print(RULE)
    if outcome.check is not None and outcome.check.passed is not None:
        print(f"[check: {'PASS' if outcome.check.passed else 'FAIL'}] {outcome.check.detail}")
    if outcome.card:
        for title, body in ((labels["what"], outcome.card.what_happened), (labels["why"], outcome.card.why_it_matters),
                            (labels["next"], outcome.card.next_step),
                            (labels["compare"], outcome.card.your_reasoning_vs_reference)):
            print(f"\n{title}\n  {body}")
    if outcome.tip_text:
        print(f"\n{labels['tip']}\n  {outcome.tip_text}")
    if outcome.flags:
        print(f"\n[flags: {', '.join(outcome.flags)}]")
    if debug and outcome.evaluation:
        ev = outcome.evaluation
        print(f"\n[debug] band={outcome.band.value} evidence_weight={outcome.evidence_weight} "
              f"correctness={ev.correctness} depth={ev.depth} clarity={ev.clarity} structure={ev.structure} "
              f"hedging={ev.hedging_ratio} rubric_level={ev.rubric_level_estimate}")
        print(f"[debug] missed={ev.key_points_missed} misconceptions={ev.misconceptions} signals={ev.behavior_signals}")
        if outcome.decision:
            print(f"[debug] decision={outcome.decision.action.value} ({outcome.decision.reason_code}) "
                  f"-> difficulty {outcome.decision.target_difficulty}")
        for row in outcome.metrics:
            print(f"[debug] {row['skill_key']}: k {row['knowledge_score_before']} -> {row['knowledge_score_after']}, "
                  f"c {row['confidence_score_before']} -> {row['confidence_score_after']}, "
                  f"level {row['provisional_level_after']}")


async def run(args) -> int:
    settings = get_settings()
    try:
        catalog = load_catalog(settings.seeds_dir)
    except CatalogError as exc:
        print(exc)
        return 2
    labels = LABELS.get(args.language, LABELS["en"])
    role = catalog.roles[args.role]
    profile = role.seniority_profiles.get(args.seniority) or next(iter(role.seniority_profiles.values()))
    plan = build_plan(catalog, args.role, args.company, args.seniority)
    store = LocalStore(settings.workdir / "cli_profile.json")

    manual_dir = settings.workdir / "manual_llm"
    kwargs = {}
    if args.provider == "anthropic":
        kwargs = {"model": settings.anthropic_model, "api_key": settings.anthropic_api_key,
                  "enable_fallbacks": settings.anthropic_enable_fallbacks}
    provider = build_provider(args.provider, manual_dir=manual_dir, **kwargs)
    if args.provider == "manual":
        provider.on_wait = lambda request, response: print(f"\n[manual LLM] read  {request}\n[manual LLM] write {response}")

    ctx = PracticeContext(
        provider=provider, skills=catalog.leaf_skills, language=args.language, seniority=args.seniority,
        difficulty_ceiling=profile.difficulty_ceiling, required_levels={s.key: s.required_level for s in plan},
        skill_weights={s.key: s.combined_weight for s in plan}, tips=list(catalog.tips.values()),
        glossary=catalog.glossary, role_family=role.family, polish_tips=args.provider == "anthropic")

    while True:
        question, familiarity, reason = pick_question(catalog, plan, store, args, profile.difficulty_ceiling)
        if question is None:
            print("No unseen question is available for your plan. Add questions to backend/seeds/questions/.")
            break
        states = store.skill_states()
        before = {k: s.provisional_level for k, s in states.items()}
        text = question.text(args.language)
        print(f"\n{RULE}\n{text.title}   [{question.subject} / {question.primary_skill} / difficulty {question.difficulty}]")
        if reason:
            print(f"{labels['why_this']}: {reason}")
        print(RULE)

        raw = input(labels["confidence"]).strip()
        confidence = int(raw) if raw.isdigit() and 1 <= int(raw) <= 5 else None
        attempt = PracticeAttempt(ctx, question, states, mode="deep" if "deep" in question.practice_modes else "quick",
                                  familiarity=familiarity, self_confidence=confidence)
        print("\n" + attempt.prompt() + "\n")

        started = time.perf_counter()
        skipped = False
        while True:
            answer = read_answer(labels["answer"])
            if answer == ":quit":
                store.save()
                return 0
            if answer == ":skip":
                skipped = True
                break
            if answer == ":hint":
                hint = attempt.next_hint()
                print(f"\n[hint {hint[0]}] {hint[1]}\n" if hint else "\n[no more hints]\n")
                continue
            if answer == ":reveal":
                print(f"\n[reference]\n{attempt.reveal_reference()}\n")
                continue
            if answer:
                break
        if skipped:
            store.data["seen_questions"].append(question.key)
            continue

        latency_ms = int((time.perf_counter() - started) * 1000)
        outcome = await attempt.submit(answer, latency_ms=latency_ms)
        all_metrics, all_usage = list(outcome.metrics), [u.as_row(attempt.mode) for u in outcome.usage]
        show_outcome(outcome, labels, args.debug)
        if outcome.band and not attempt.reference_revealed and input("\nShow the reference solution? [y/N] ").lower().startswith("y"):
            print(f"\n[reference]\n{attempt.reveal_reference()}")

        while outcome.follow_up:
            print(f"\n{RULE}\n{labels['follow']}\n{RULE}\n{outcome.follow_up}\n")
            started = time.perf_counter()
            answer = read_answer(labels["answer"])
            if answer in (":quit", ":skip", ""):
                break
            outcome = await attempt.submit_follow_up(answer, latency_ms=int((time.perf_counter() - started) * 1000))
            all_metrics += outcome.metrics
            all_usage += [u.as_row(attempt.mode) for u in outcome.usage]
            show_outcome(outcome, labels, args.debug)

        # level changes and retention scheduling
        print(f"\n{RULE}")
        for key in dict.fromkeys(row["skill_key"] for row in all_metrics):
            state = states[key]
            status = scores.evidence_status(state, ctx.required_levels.get(key, 2))
            note = "" if status.value == "assessed" else f" ({labels['provisional']})"
            print(f"  {catalog.skills[key].label}: {labels['level']} {before.get(key) or '-'} -> "
                  f"{state.provisional_level}{note}")
            due = plan_router.schedule_retention(level_before=before.get(key), level_after=state.provisional_level,
                                                 today=date.today())
            if due and status.value == "assessed":
                store.set_retention(key, due, 0)
        store.put_skill_states(states)
        store.record_attempt(attempt.attempt_row(duration_ms=latency_ms), all_metrics, all_usage,
                             attempt.band.value if attempt.band else None)
        store.save()
        attempt_path = settings.workdir / "attempts" / f"{len(store.data['attempts']):04d}_{question.key}.json"
        attempt_path.parent.mkdir(parents=True, exist_ok=True)
        attempt_path.write_text(json.dumps(store.data["attempts"][-1], ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{labels['done']}  ({attempt_path.name}; model cost so far ${store.total_cost_usd():.4f})")

        if args.once or input("\nAnother question? [Y/n] ").lower().startswith("n"):
            break
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    settings = get_settings()
    parser.add_argument("--language", choices=["en", "he"], default=settings.default_language)
    parser.add_argument("--provider", choices=["manual", "anthropic"], default=settings.llm_provider)
    parser.add_argument("--role", default=settings.default_role)
    parser.add_argument("--company", default=settings.default_company)
    parser.add_argument("--seniority", default="student")
    parser.add_argument("--minutes", type=int, default=30, help="minutes available today")
    parser.add_argument("--question", help="practice one specific question key")
    parser.add_argument("--once", action="store_true", help="stop after one question")
    parser.add_argument("--debug", action="store_true", help="show scores, decisions and metrics")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
