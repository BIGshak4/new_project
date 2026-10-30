"""Reproduce actual Python checks against independent oracles."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("intake_20261030_code", BANK.parent / "backend/tests/test_preparation_20261030_code.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def run_checks():
    return {"status": "passed", "checked_on": "2026-10-30", **checks.check_binary_cases(),
            "scope": "Actual Python model and independent oracle. Human professional review pending. Supplied C was not compiled."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-138-verification.json").write_text(json.dumps(result, indent=2) + "\n", "utf-8")
    print(json.dumps(result))
