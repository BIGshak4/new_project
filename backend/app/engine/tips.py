"""Tip matching and composition (AI_Engine_Spec §6.4, §6.5).

Let the candidate struggle with the problem, never with the process. A tip is about
how they work, never the answer. Selection is rules; the model only polishes one
sentence, and the tip still works if that call fails.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.engine import i18n
from app.engine.evaluator import BEHAVIOR_SIGNALS
from app.engine.providers import LLMError, LLMRequest, Provider
from app.schemas.bank import Tip
from app.schemas.engine import Action, Band, Evaluation

MID_SESSION_MIN_SEVERITY = 4
DEFAULT_COOLDOWN_TURNS = 5
DEFAULT_EFFECTIVENESS = 0.5

_OPS = {
    "<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
    "in": lambda a, b: a in b, "not_in": lambda a, b: a not in b,
    "contains": lambda a, b: b in a,
}


def signals_from(evaluation: Evaluation, *, band: Band, archetype: str, hint_level: int = 0,
                 confidence: float | None = None, self_confidence: int | None = None,
                 mode: str = "deep", check_passed: bool | None = None) -> dict:
    """Flatten everything a tip can trigger on into one dictionary."""
    signals = {
        "correctness": evaluation.correctness, "depth": evaluation.depth, "clarity": evaluation.clarity,
        "structure": evaluation.structure, "tradeoff_reasoning": evaluation.tradeoff_reasoning,
        "risk_awareness": evaluation.risk_awareness, "hedging_ratio": evaluation.hedging_ratio,
        "band": band.value, "question_archetype": archetype, "hint_level": hint_level, "mode": mode,
        "confidence": confidence, "self_confidence": self_confidence, "check_passed": check_passed,
        "misconceptions": list(evaluation.misconceptions), "behavior_signals": list(evaluation.behavior_signals),
    }
    # behavior signals are flags: absent means False. Every other signal is None when unknown,
    # and an unknown signal never satisfies a condition.
    for signal in BEHAVIOR_SIGNALS:
        signals[signal] = signal in evaluation.behavior_signals
    # calibration: how far the self-rating was from the outcome (AI_Engine_Spec §2.10)
    if self_confidence is not None:
        signals["calibration_gap"] = round(self_confidence / 5.0 - evaluation.correctness, 3)
    return signals


def _holds(condition: dict, signals: dict) -> bool:
    op = _OPS.get(condition.get("op", "=="))
    if op is None:
        return False
    value = signals.get(condition["signal"])
    if value is None:
        return False
    try:
        return bool(op(value, condition["value"]))
    except TypeError:
        return False


def matches(tip: Tip, signals: dict) -> bool:
    conditions = tip.trigger_conditions
    any_of, all_of = conditions.get("any_of", []), conditions.get("all_of", [])
    if not any_of and not all_of:
        return False
    return (not any_of or any(_holds(c, signals) for c in any_of)) and all(_holds(c, signals) for c in all_of)


@dataclass
class TipChoice:
    tip: Tip
    timing: str                        # mid_session | post_session
    score: float


def select_tip(tips: list[Tip], signals: dict, *, turn_index: int, last_delivered_turn: dict[str, int],
               skill_key: str | None = None, role_family: str | None = None, timing: str = "mid_session",
               last_action: Action | None = None) -> TipChoice | None:
    """At most one tip per turn, ranked by severity x effectiveness (§6.4, §6.5)."""
    # stay out of the way when it is going well
    if timing == "mid_session" and (last_action == Action.ESCALATE or signals.get("band") == Band.STRONG.value):
        return None
    candidates: list[TipChoice] = []
    for tip in tips:
        if not tip.is_active or not matches(tip, signals):
            continue
        if tip.delivery_timing not in ("both", timing):
            continue
        if timing == "mid_session" and tip.severity < MID_SESSION_MIN_SEVERITY:
            continue                    # lighter tips are held for the report
        if tip.applicable_skills and skill_key not in tip.applicable_skills:
            continue
        if tip.applicable_families and role_family and role_family not in tip.applicable_families \
                and "general" not in tip.applicable_families:
            continue
        cooldown = tip.trigger_conditions.get("cooldown_turns", DEFAULT_COOLDOWN_TURNS)
        last = last_delivered_turn.get(tip.key)
        if last is not None and turn_index - last < cooldown:
            continue
        score = tip.severity * (tip.effectiveness_score if tip.effectiveness_score is not None else DEFAULT_EFFECTIVENESS)
        candidates.append(TipChoice(tip=tip, timing=timing, score=score))
    if not candidates:
        return None
    return max(candidates, key=lambda c: (c.score, c.tip.severity, c.tip.key))


def render(tip: Tip, language: str, placeholders: dict[str, str] | None = None) -> str:
    template = tip.templates.get(language) or tip.templates.get("en") or next(iter(tip.templates.values()))
    values = placeholders or {}
    text = re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(values.get(m.group(1), "")), template)
    return re.sub(r"\s{2,}", " ", text).strip()


async def compose(provider: Provider | None, choice: TipChoice, *, language: str,
                  placeholders: dict[str, str] | None = None, tone: str | None = None) -> str:
    """Render the template, then let the model polish it. The rendered text is the fallback."""
    rendered = render(choice.tip, language, placeholders)
    if provider is None:
        return rendered
    request = LLMRequest(
        role="tip", system=[i18n.stable_system_block("tip", language)], prompt_version=i18n.prompt_version("tip"),
        user=f"<tone>{tone or 'direct and encouraging'}</tone>\n<tip>\n{rendered}\n</tip>",
    )
    try:
        response = await provider.complete(request)
    except LLMError:
        return rendered
    polished = " ".join(response.text.split())
    return polished if 10 <= len(polished) <= 400 else rendered


def tips_for_gaps(tips: list[Tip], gap_skills: list[str], limit: int = 3) -> list[Tip]:
    """Post-session: tips whose improves_skills cover the largest weighted gaps (§7 step 6)."""
    ranked = []
    for tip in tips:
        covered = [gap_skills.index(s) for s in tip.improves_skills if s in gap_skills]
        if covered and tip.is_active:
            ranked.append((min(covered), -tip.severity, tip.key, tip))
    return [entry[3] for entry in sorted(ranked)[:limit]]
