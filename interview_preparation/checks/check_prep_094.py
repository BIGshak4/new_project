"""Independent string oracle for all byte values; strings only in test harness."""
import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / 'solutions'))
from prep_094_reverse_byte import reverse_byte

for value in range(256):
    result = reverse_byte(value)
    assert result == int(f'{value:08b}'[::-1], 2)
    assert reverse_byte(result) == value
    assert result.bit_count() == value.bit_count()
    assert reverse_byte(value ^ 255) == result ^ 255
    assert 0 <= result <= 255
    for bit in range(8):
        assert ((value >> bit) & 1) == ((result >> (7 - bit)) & 1)
assert reverse_byte(0b01101011) == 0b11010110
invalid = (-1, 256, 65535, True, None, 1.5, '01101011')
for value in invalid:
    try:
        reverse_byte(value)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid byte accepted')
record = {
    'question_id': 'PREP-094', 'checked_on': '2026-10-24', 'status': 'passed',
    'exhaustive_valid_inputs': 256, 'bit_position_checks': 2048,
    'invalid_inputs_rejected': len(invalid), 'involution_popcount_complement_checks': 256,
    'source_example': {'input': '01101011', 'output': '11010110'},
    'oracle': 'Independent fixed-width 8-character string reversal; strings and arrays are used only by verification, not the solution.',
    'scope': 'Unsigned 8-bit values, Python execution; no fixed-width language compilation or runtime benchmark.'
}
(BANK / 'checks/prep-094-verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
