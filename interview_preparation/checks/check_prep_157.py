"""Check every input row against independent selector semantics."""
import importlib.util
import itertools
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mux157', BANK/'solutions/prep_157_two_input_mux.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def verify():
    rows = 0
    for d0,d1,s in itertools.product((0,1),repeat=3):
        assert model.mux(d0,d1,s) == [d0,d1][s]
        rows += 1
    for values in ((2,0,0),(0,-1,1),(0,0,2)):
        try:
            model.mux(*values)
        except ValueError:
            pass
        else:
            raise AssertionError(values)
    return {'status':'passed','binary_truth_table_rows':rows,'invalid_rows':3,
            'scope':'Ideal combinational Boolean model; no delay, glitches or transistor test.'}


if __name__ == '__main__':
    result = verify()
    (BANK/'checks/prep-157-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result)
