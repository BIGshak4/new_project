"""Reproduce actual Python model checks against independent oracles."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("intake_20261030_batch40_code", BANK.parent / "backend/tests/test_preparation_20261030_batch40_code.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def run_checks():
    return {"status": "passed", "checked_on": "2026-10-30", **checks.check_costume_cases(),
            "scope": "Actual Python models versus independent oracles; no native compilation, benchmark or human approval claimed."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-148-verification.json").write_text(json.dumps(result, indent=2) + "\n", "utf-8")
    print(json.dumps(result))
