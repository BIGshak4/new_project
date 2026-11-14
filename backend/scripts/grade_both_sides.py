"""Both sides of the grader at once, on the real model: answers that are right but short (must be STRONG) and
answers that are not right (must not be). Shaked, 2026-11-14: a correct answer must not get a bad grade for what it
left out; and a wrong or incomplete one must not ride along.

    uv run python scripts/grade_both_sides.py [repeats]        # default 3; about a cent per 4 gradings

Each answer is graded `repeats` times, because the judge is not perfectly repeatable and a prompt that is right
"usually" is not right. In memory, nothing is saved. Run it before and after any change to the evaluator prompt or
to the band thresholds, next to scripts/p2_review_set.py.
"""
import asyncio
import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")


from app.config import get_settings  # noqa: E402
from app.engine import evaluator, i18n, scores  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.checks import run_check  # noqa: E402
from app.engine.params import DEFAULT_PARAMS  # noqa: E402
from app.runtime import make_provider  # noqa: E402

CODE = "def count_set_bits(x):\n    count = 0\n    while x != 0:\n        x &= x - 1\n        count += 1\n    return count"
BUGGY = "def count_set_bits(x):\n    total = 0\n    for i in range(31):\n        total += (x >> i) & 1\n    return total"
NAND = "nA = NAND(A,A), nB = NAND(B,B), R = NAND(nA,nB), T = NAND(E,R), Y = NAND(T,T)."
MAJ, CNT, SH, ND = "example-sensor-majority", "example-count-set-bits", "example-setup-hold-calculation", "example-nand-only-enable"
RIGHT = [
    (MAJ, "expression only", "alarm = AB + AC + BC"),
    (MAJ, "expression + XOR line, no table", "alarm = AB + AC + BC. XOR is not enough: it is 1 when exactly one sensor is on, and 0 when exactly two are on."),
    (MAJ, "expression + table, no XOR line", "alarm = AB + AC + BC. Rows 000..111: 0,0,0,1,0,1,1,1."),
    (CNT, "correct code only", CODE),
    (CNT, "correct code + complexity", CODE + "\nTime O(number of set bits), space O(1)."),
    (SH, "the three numbers only", "Tmin = 1.40 ns, fmax = 714 MHz, hold slack = +0.03 ns."),
    (SH, "numbers + one-line hold answer", "Tmin = 1.40 ns, fmax = 714 MHz, hold slack = +0.03 ns. No, a slower clock does not fix a hold violation."),
    (ND, "correct gates only", NAND),
    (ND, "correct gates + De Morgan line", NAND + " R is A OR B by De Morgan."),
]
NOT_RIGHT = [
    (SH, "Tmin right, hold slack wrong sign", "Tmin = 1.40 ns, fmax = 714 MHz, hold slack = -0.03 ns so the path fails hold."),
    (SH, "only Tmin of three quantities", "Tmin = 1.40 ns."),
    (SH, "numbers right, wrong hold conclusion", "Tmin = 1.40 ns, fmax = 714 MHz, hold slack = +0.03 ns. Yes, lowering the frequency fixes a hold violation."),
    (MAJ, "wrong expression (a pair missing)", "alarm = AB + AC"),
    (MAJ, "right expression, claims XOR works too", "alarm = AB + AC + BC. A three-input XOR would also work, since it is 1 when more than one input is 1."),
    (CNT, "code with a bug (misses the top bit)", BUGGY),
    (ND, "inverter and OR gate (breaks the constraint)", "R = A OR B, T = NAND(E, R), Y = NOT(T)."),
]


async def main() -> None:
    catalog = load_catalog(BACKEND / "seeds")
    provider = make_provider(get_settings())
    repeats = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    async def grade(key, answer):
        question = catalog.questions[key]
        skill = catalog.leaf_skills[question.primary_skill]
        check = run_check(question.deterministic_check, answer) if question.deterministic_check else None
        result = await evaluator.evaluate(provider, question_context=evaluator.question_block(question, "en", skill),
                                          known_error_keys={e.key for e in question.common_errors}, language="en",
                                          difficulty=question.difficulty, answer=answer, check=check, glossary=catalog.glossary)
        if not result.ok:
            return "FAILED", None, None
        ev = scores.apply_check_result(result.evaluation, check, DEFAULT_PARAMS)
        core = bool(set(ev.misconceptions) & question.core_misconception_keys)
        return scores.classify_band(ev, core, DEFAULT_PARAMS).value, result.evaluation.correctness, ev.depth

    print("grader:", i18n.prompt_version("evaluator"), "| repeats:", repeats)
    for title, cases, want in (("RIGHT BUT SHORT (must be STRONG)", RIGHT, True), ("NOT RIGHT (must not be STRONG)", NOT_RIGHT, False)):
        print("\n" + title)
        bad = 0
        for key, label, answer in cases:
            results = await asyncio.gather(*(grade(key, answer) for _ in range(repeats)))
            bands = Counter(r[0] for r in results)
            raw = sorted(r[1] for r in results if r[1] is not None)
            wrong = sum(n for band, n in bands.items() if (band == "STRONG") != want)
            bad += wrong
            print(f"  {'ok ' if not wrong else 'BAD'} {dict(bands)}  judge correctness {raw}  {key.replace('example-', '')}: {label}")
        print(f"  -> {bad} of {len(cases) * repeats} gradings on the wrong side")

asyncio.run(main())
