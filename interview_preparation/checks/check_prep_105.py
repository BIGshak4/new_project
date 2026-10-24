"""Check the actual signed-int32 bit test against independent fixed-width digit counting."""
import importlib.util
import itertools
import json
import random
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def verify():
    spec = importlib.util.spec_from_file_location('onehot105', BANK / 'solutions/prep_105_signed_one_hot.py')
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)

    def signed(raw):
        return raw if raw < 2 ** 31 else raw - 2 ** 32

    def oracle(raw):
        return sum((raw >> position) % 2 for position in range(32)) == 1

    for raw in range(1 << 16):
        assert model.is_one_bit_active(raw) == oracle(raw)
    for position in range(32):
        assert model.is_one_bit_active(signed(1 << position))
    for left, right in itertools.combinations(range(32), 2):
        assert not model.is_one_bit_active(signed((1 << left) | (1 << right)))
    rng = random.Random(105)
    for _ in range(10000):
        raw = rng.randrange(1 << 32)
        assert model.is_one_bit_active(signed(raw)) == oracle(raw)
    assert model.is_one_bit_active(-(1 << 31))
    assert not model.is_one_bit_active(0) and not model.is_one_bit_active(-1)
    assert model.is_one_bit_active(0x00080000) and not model.is_one_bit_active(0x000C0000)
    for value in (True, 1.5, None, -(1 << 31) - 1, 1 << 31):
        try:
            model.is_one_bit_active(value)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid int32 accepted')
    return {'passed': True, 'all_low_16bit_patterns': 65536, 'one_hot_patterns': 32,
            'two_hot_patterns': 496, 'random_full_width_patterns': 10000,
            'sign_bit_and_zero_and_source_examples': True, 'executed': 'actual Python model',
            'cpp_compiled': False, 'scope': 'Fixed-width bit pattern logic; Python validation rejects non-int32 inputs.'}


if __name__ == '__main__':
    result = verify()
    (BANK / 'checks/prep-105-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
