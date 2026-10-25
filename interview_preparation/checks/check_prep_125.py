"""Execute both expanded four-op programs against arithmetic oracles."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("batch11_checks", BANK.parent / "backend/tests/test_preparation_batch11_code.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def run_checks():
    result = checks.check_machine_cases()
    checks.test_jnz_uses_immediately_previous_instruction_result_and_has_no_register_argument()
    checks.test_machine_rejects_underflow_invalid_inputs_and_missing_termination()
    return {"question_id": "PREP-125", "checked_on": "2026-10-25", "status": "passed", **result,
            "oracle": "Python multiplication and absolute difference, independent of the expanded ISA programs; strict instruction, underflow, last-result branch and halting checks.",
            "scope": "Educational four-op interpreter execution on unbounded natural registers; not compiled machine assembly, hardware timing or human professional approval."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-125-verification.json").write_text(json.dumps(result, indent=2) + "\n", "utf-8")
    print(json.dumps(result))
