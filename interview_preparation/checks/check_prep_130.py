"""All eight-bit inputs checked against a numeric max oracle."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("clamp130", BANK / "solutions/prep_130_eight_bit_lower_clamp.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    outputs = []
    for value in range(256):
        actual = model.clamp_lower64(value)
        assert actual == max(value, 64)
        assert model.clamp_lower64(actual) == actual
        assert 64 <= actual <= 255
        outputs.append(actual)
    assert outputs == sorted(outputs)
    assert outputs[63:66] == [64, 64, 65]
    rejected = 0
    for value in (-1, 256, True, "64"):
        try:
            model.clamp_lower64(value)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(value)
    return {"question_id": "PREP-130", "status": "passed", "input_vectors": 256,
            "idempotence_checks": 256, "monotonicity_checked": True, "invalid_inputs_rejected": rejected,
            "scope": "Exhaustive Python Boolean gate model against unsigned integer max, including equality/boundaries. No minimum circuit, HDL, hazards, synthesis or physical timing claim; human review pending."}


if __name__ == "__main__":
    evidence = run_checks()
    (BANK / "checks/prep-130-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))
