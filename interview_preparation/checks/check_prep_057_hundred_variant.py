"""Reproduce hundred-prisoner fair schedules and the missing-person bound."""

import importlib.util
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "batch20_root_checks", root / "backend/tests/test_preparation_batch20_root_v2.py"
)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)

if __name__ == "__main__":
    print(json.dumps(checks.prisoner_checks(), indent=2))
