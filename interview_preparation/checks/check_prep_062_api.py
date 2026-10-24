"""API-model trajectories compared with a separate linear-time formula."""
import json
import sys
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_062_api_robots import RobotProgram, meeting_offset, simulate


def main():
    cases = 0
    for distance in range(1, 257):
        for origin in (-1000, 0, 37):
            for swapped in (False, True):
                assert simulate(distance, origin, swapped) == 4 * distance - 2
                cases += 1
    assert simulate(0) == 0
    program = RobotProgram()
    assert program.command(True, False) == "move_right"
    assert program.command(False, False) == "no_operation"
    assert program.command(False, False) == "move_right"
    assert program.command(True, False) == "move_right"
    assert program.command(False, False) == "move_right"
    assert program.command(False, True) == "stop"
    # Harness collision arithmetic supports meetings within a tick, not only endpoints.
    assert meeting_offset(-1, 2) == Fraction(1, 2)
    assert meeting_offset(1, -2) == Fraction(1, 2)
    assert meeting_offset(-1, -2) is None
    assert meeting_offset(-3, 2) is None
    assert meeting_offset(0, 0) == 0
    result = {"question_id": "PREP-062", "variant": "explicit_API_free_queries",
              "status": "passed", "trajectory_cases": cases,
              "distance_range": [1, 256], "zero_separation": "passed",
              "scope": "Motion/wait one tick; instantaneous queries/control; synchronized common orientation. Old paid-instruction model unchanged."}
    (BANK / "checks/prep-062-api-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
