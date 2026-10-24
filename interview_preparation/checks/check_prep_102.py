"""Compare the actual bitmap allocator against a separate set-of-indices oracle."""
import importlib.util
import json
import random
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def verify():
    spec = importlib.util.spec_from_file_location('allocator102', BANK / 'solutions/prep_102_bitmap_allocator.py')
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    pool = model.Pool32()
    assert not hasattr(pool, '__dict__') and pool.used == 0
    for index in range(32):
        assert pool.malloc_index() == index
    assert pool.used == 0xFFFFFFFF and pool.malloc_index() == -1
    assert pool.free_index(31) and pool.malloc_index() == 31
    assert pool.free_index(0) and not pool.free_index(0)
    for value in (-1, 32, 999, True, 1.5, None):
        before = pool.used
        assert not pool.free_index(value) and pool.used == before
    # Every occupancy pattern in a 16-slot subspace, with the upper half occupied.
    for mask in range(1 << 16):
        pool.used = mask | 0xFFFF0000
        expected = next((index for index in range(16) if not (mask >> index) & 1), -1)
        assert pool.malloc_index() == expected
    rng = random.Random(102)
    free = set(range(32))
    pool = model.Pool32()
    for _ in range(50000):
        if rng.randrange(2):
            expected = min(free) if free else -1
            actual = pool.malloc_index()
            assert actual == expected
            if actual != -1:
                free.remove(actual)
        else:
            index = rng.randrange(-2, 34)
            expected = 0 <= index < 32 and index not in free
            assert pool.free_index(index) is expected
            if expected:
                free.add(index)
        assert pool.used == sum(1 << index for index in set(range(32)) - free)
        assert 0 <= pool.used <= model.MASK32
    return {'passed': True, 'subspace_occupancy_states': 65536, 'random_operations': 50000,
            'full_and_empty_and_invalid_frees': True, 'executed': 'actual Python model',
            'cpp_compiled': False, 'scope': 'Logical bitmap allocation; not a concurrent allocator or physical memory test.'}


if __name__ == '__main__':
    result = verify()
    (BANK / 'checks/prep-102-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
