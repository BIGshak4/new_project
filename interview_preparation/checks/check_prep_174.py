"""Executed independent batch70 verification wrapper."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("batch70checks", HERE / "batch70_hardware_checks.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run_checks():
    return module.CHECKS["174"]()


if __name__ == "__main__":
    result = run_checks()
    (HERE / "prep-174-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
