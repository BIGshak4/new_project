"""Reproduce PREP-098 checks using the independent backend oracle harness."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
ROOT = BANK.parent
spec = importlib.util.spec_from_file_location("batch20_code_checks", ROOT / "backend/tests/test_preparation_batch20_code.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checked = module.check_merge_cases()
record = {"question_id": "PREP-098", "checked_on": "2026-10-24", "status": "passed",
          "exhaustive_cases": checked, "oracle": 'Independent frequency reconstruction over all sorted arrays of lengths 0..5 over {-2,0,3}.',
          "scope": "Actual proposed Python implementation executed; includes empty/boundary inputs, exact large integers and input preservation. No fixed-width compilation, runtime benchmark or human professional approval."}
(BANK / "checks/prep-098-verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
