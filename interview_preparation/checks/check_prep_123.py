"""Reproduce the actual postfix evaluator against an independent recursive oracle."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("batch11_checks", BANK.parent / "backend/tests/test_preparation_batch11_code.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def run_checks():
    return {"question_id": "PREP-123", "checked_on": "2026-10-25", "status": "passed",
            **checks.check_postfix_cases(),
            "oracle": "Independent recursive right-to-left parse/evaluation, not a second forward stack implementation.",
            "scope": "Actual Python integer implementation executed. No fixed-width compilation, benchmark or human professional approval."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-123-verification.json").write_text(json.dumps(result, indent=2) + "\n", "utf-8")
    print(json.dumps(result))
