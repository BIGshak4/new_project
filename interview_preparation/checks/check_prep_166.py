"""Reproduce the executed independent mathematical/model checks."""

import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "batch70_reasoning_checks",
    BANK.parent / "backend/tests/test_preparation_20261030_batch70_reasoning.py",
)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def run_checks():
    return checks.check_game()


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-166-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
