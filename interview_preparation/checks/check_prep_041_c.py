"""Reproduce PREP-041-C using independent backend oracle checks."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
ROOT = BANK.parent
spec = importlib.util.spec_from_file_location("batch30_code_checks", ROOT / "backend/tests/test_preparation_batch30_code.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checked = module.check_missing_cases()
record = {"question_id": 'PREP-041-C', "checked_on": "2026-10-24", "status": "passed",
          "exhaustive_or_operation_cases": checked, "oracle": 'Independent linear membership oracle over 46,233 valid zero-based permutations plus 400 seeded cases; compare the actual flags and XOR implementations and verify input preservation.',
          "scope": "Actual proposed Python executed, no fixed-width compilation, Python heap-budget claim, performance benchmark or human professional approval."}
(BANK / "checks/prep-041-c-verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
