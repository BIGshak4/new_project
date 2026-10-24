"""Reproduce PREP-117 using independent backend oracle checks."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
ROOT = BANK.parent
spec = importlib.util.spec_from_file_location("batch30_code_checks", ROOT / "backend/tests/test_preparation_batch30_code.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checked = module.check_pool_cases()
record = {"question_id": 'PREP-117', "checked_on": "2026-10-24", "status": "passed",
          "exhaustive_or_operation_cases": checked, "oracle": 'Independent deque of free slots plus a dictionary of allocated uint64 payloads; 10,065 valid operations, all 64 slots drained, full sentinel and 10,000 seeded actions; every allocated payload preserved.',
          "scope": "Actual proposed Python executed, no fixed-width compilation, Python heap-budget claim, performance benchmark or human professional approval."}
(BANK / "checks/prep-117-verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
