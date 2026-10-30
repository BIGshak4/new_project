"""Independent all-interval oracle and a forward-only iterator contract."""
import importlib.util
import json
from itertools import product
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("stream_maximum", BANK / "solutions/prep_072_stream_maximum_subarray_batch90.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class ForwardOnly:
    def __init__(self, values):
        self.iterator = iter(values)
        self.iterations = 0
        self.consumed = 0

    def __iter__(self):
        self.iterations += 1
        assert self.iterations == 1, "Input must not be replayed"
        def cursor():
            for value in self.iterator:
                self.consumed += 1
                yield value
        return cursor()


def verify():
    checked = 0
    for length in range(1, 8):
        for values in product((-2, -1, 0, 1, 2), repeat=length):
            expected = min((-sum(values[start:end]), start, end)
                           for start in range(length) for end in range(start + 1, length + 1))
            expected = (-expected[0], expected[1], expected[2])
            stream = ForwardOnly(values)
            assert model.stream_maximum_subarray(stream) == expected, values
            assert stream.consumed == length
            checked += 1
    try:
        model.stream_maximum_subarray(iter(()))
    except ValueError:
        pass
    else:
        raise AssertionError("empty input was accepted")
    return {"status": "passed", "cases": checked, "domain": "All nonempty arrays over -2,-1,0,1,2 at lengths 1..7",
            "oracle": "Enumerate every nonempty interval; choose maximal sum, earliest start, then earliest exclusive end",
            "stream_contract": "One iteration, each item consumed once, no indexing, length query or replay",
            "empty_input": "ValueError", "limitations": "Finite exact Python integer model; no bounded-width C overflow or infinite-stream termination claim."}


if __name__ == "__main__":
    result = verify()
    Path(__file__).with_name("prep-072-stream-batch90-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
