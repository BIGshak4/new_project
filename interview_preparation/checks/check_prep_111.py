"""Reproduce PREP-111 using the independent backend oracle harness."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
ROOT = BANK.parent
spec = importlib.util.spec_from_file_location("batch10_code_checks", ROOT / "backend/tests/test_preparation_batch10_code.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checked = module.check_bitmap_cases()
record = {"question_id": "PREP-111", "checked_on": "2026-10-24", "status": "passed",
          "exhaustive_cases": checked, "oracle": 'Independent per-pixel arithmetic oracle on 18224 valid lines plus500seeded initial byte buffers; full-buffer equality includes row-padding, unusedbits and trailingbytes.',
          "scope": "Actual proposed Python implementation executed; no physical screen driver, fixed-width compilation, performance benchmark or human professional approval."}
(BANK / "checks/prep-111-verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
