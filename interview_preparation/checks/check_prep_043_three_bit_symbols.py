"""Compare prefix states with independent full-history suffix matching."""
import importlib.util
import itertools
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("symbols", BANK / "solutions/prep_043_three_bit_symbols.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def verify():
    transitions = 0
    for target in itertools.product(range(8), repeat=4):
        detector = model.FourSymbolDetector(target)
        for state in range(5):
            for symbol in range(8):
                history = target[:state] + (symbol,)
                candidates = [size for size in range(min(4, len(history)) + 1)
                              if tuple(history[len(history) - size:]) == target[:size]]
                expected = max(candidates)
                detector.state = state
                flag = detector.step(symbol)
                assert detector.state == expected and flag == int(expected == 4)
                transitions += 1
    streams = symbols = 0
    for target in itertools.product(range(2), repeat=4):
        for length in range(10):
            for word in itertools.product(range(2), repeat=length):
                detector = model.FourSymbolDetector(target)
                history = []
                for symbol in word:
                    history.append(symbol)
                    assert detector.step(symbol) == int(tuple(history[-4:]) == target and len(history) >= 4)
                    symbols += 1
                assert detector.step(7, reset=True) == 0 and detector.state == 0
                streams += 1
    repeat = model.FourSymbolDetector([1, 1, 1, 1])
    assert [repeat.step(1) for _ in range(6)] == [0, 0, 0, 1, 1, 1]
    overlap = model.FourSymbolDetector([1, 2, 1, 2])
    assert [overlap.step(x) for x in [1, 2, 1, 2, 1, 2]] == [0, 0, 0, 1, 0, 1]
    return {"status": "passed", "all_4096_target_transition_rows": transitions,
            "binary_target_stream_pairs": streams, "stream_symbols": symbols,
            "reset_checks": streams, "scope": "Python prefix-state model, no HDL compilation or physical timing"}


if __name__ == "__main__":
    result = verify()
    (BANK / "checks/prep-043-three-bit-symbols-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
