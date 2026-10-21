"""Independent finite DP and all adversarial replies for exact-target 21."""
from functools import cache
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("game21", BANK / "solutions/prep_060_game_twenty_one.py")
solution = module_from_spec(spec)
spec.loader.exec_module(solution)


@cache
def oracle(total):
    if total == 21:
        return False
    # State is winning iff some legal move leaves no winning reply.
    return any(not oracle(total + step) for step in (1, 2, 3) if total + step <= 21)


def run():
    for total in range(22):
        move = solution.winning_move(total)
        assert (move is not None) == oracle(total)
        if move is not None:
            assert 1 <= move <= 3 and total + move <= 21
            assert not oracle(total + move)
    adversarial = 0
    for replies in product((1, 2, 3), repeat=5):
        total = solution.winning_move(0)
        assert total == 1
        for reply in replies:
            total += reply
            assert total < 21  # Opponent never reaches target first.
            response = solution.complement_reply(reply)
            assert total + response <= 21
            assert solution.winning_move(total) == response
            total += response
            assert total in (5, 9, 13, 17, 21)
        assert total == 21
        adversarial += 1
    rejected = 0
    for value in (-1, 22, True, False, 1.0, None, "0"):
        try:
            solution.winning_move(value)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(value)
    for value in (0, 4, -1, True, 2.0, None):
        try:
            solution.complement_reply(value)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(value)
    result = dict(question_id="PREP-060", checked_on="2026-10-21", status="passed_python_model",
                  dp_positions=22, complete_adversarial_sequences=adversarial, invalid_inputs=rejected,
                  losing_totals=[t for t in range(21) if not oracle(t)],
                  method="Independent minimax DP over all legal positions, plus all 3^5 opponent response sequences against the complement strategy.",
                  limits="Finite exact-game verification, not human professional approval or live learner activity.")
    (BANK / "checks/prep-060-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
