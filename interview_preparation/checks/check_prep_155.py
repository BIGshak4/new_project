"""Independent truth tables for arithmetic scalar gates."""
import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gates155', BANK/'solutions/prep_155_arithmetic_boolean_gates.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def verify():
    count = 0
    for x in (0, 1):
        for y in (0, 1):
            expected = (int(not x), int(bool(x) and bool(y)), int(bool(x) or bool(y)), int(x != y))
            assert model.gates(x, y) == expected
            assert all(value in (0, 1) for value in model.gates(x, y))
            count += 1
    assert model.gates(2, 1) != (0, 0, 0, 0)  # Out-of-domain inputs have no gate contract.
    return {'status':'passed','input_pairs':count,'truth_table_outputs':4*count,
            'scope':'All scalar binary inputs; no physical hardware or arbitrary-word Boolean contract.'}


if __name__ == '__main__':
    result = verify()
    (BANK/'checks/prep-155-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result)
