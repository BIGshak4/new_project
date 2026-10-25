"""Reproduce the owned software model against its independent oracle."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("batch20_code_v2", BANK.parent / "backend/tests/test_preparation_batch20_code_v2.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def run_checks():
    return {"status": "passed", "checked_on": "2026-10-25", **checks.check_mirror_cases(),
            "scope": "Actual Python model executed against independent oracle. C source, where provided, was not compiled. No benchmark or human professional approval."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-094-c-mirror-verification.json").write_text(json.dumps(result, indent=2) + "\n", "utf-8")
    print(json.dumps(result))
