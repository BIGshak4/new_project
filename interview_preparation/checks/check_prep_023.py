"""Compare the bit expression with independently generated powers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'solutions'))
from prep_023_power_of_two import is_power_of_two

powers = {2 ** k for k in range(17)}
for n in range(-65536, 65537):
    assert is_power_of_two(n) == (n in powers), n
for k in [31, 32, 63, 64, 127, 128, 1024, 4096]:
    p = 2 ** k
    assert is_power_of_two(p)
    assert not is_power_of_two(p - 1)
    assert not is_power_of_two(p + 1)
    assert not is_power_of_two(-p)
assert [is_power_of_two(n) for n in [0, 1, 2, 3, 12, 16]] == [False, True, True, False, False, True]
print('PASS: 131073 consecutive integers, 32 large boundary cases and named examples. Correctness only, not a constant-time benchmark for arbitrary-size Python integers.')
