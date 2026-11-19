"""Exact checks of the three proposed puzzle solutions."""
import json
from fractions import Fraction
from itertools import product
from pathlib import Path


def cylinder():
    # One unit in these coordinates is a whole turn or a full height.
    sectors = [(Fraction(i, 4), Fraction(i + 1, 4)) for i in range(4)]
    layers = [(Fraction(i, 2), Fraction(i + 1, 2)) for i in range(2)]
    pieces = list(product(sectors, layers))
    for partition in (sectors, layers):
        assert partition[0][0] == 0 and partition[-1][1] == 1
        assert all(a[1] == b[0] for a, b in zip(partition, partition[1:]))
    for (angle_lo, angle_hi), (z_lo, z_hi) in pieces:
        assert angle_hi-angle_lo == Fraction(1, 4)
        assert z_hi-z_lo == Fraction(1, 2)
    return {'congruent_quarter_sectors_at_half_height': len(pieces),
            'fraction_of_volume_in_each': '1/8'}


def cards():
    solutions = []
    for kings, queens, jacks in product(range(1, 11), repeat=3):
        aces = 13-kings-queens-jacks
        counts = (queens, kings, jacks, aces)
        if aces > 0 and len(set(counts)) == 4 and kings+queens == 5 and jacks+queens == 6:
            solutions.append(counts)
    assert sorted(solutions) == [(1, 4, 5, 3), (4, 1, 2, 6)]
    assert [counts[2] for counts in solutions if 2 in counts] == [2]
    assert not any(max(counts) <= 4 for counts in solutions)
    return {'ordered_columns': ['queens', 'kings', 'jacks', 'aces'],
            'assignments_meeting_clues': sorted(solutions), 'guaranteed_pair_rank_if_present': 'jacks'}


def hourglasses():
    # A full glass can be started only at an observed event (or t=0).
    def observe(starts):
        events = {0}
        next_free = {4: 0, 7: 0}
        for start, duration in starts:
            assert start in events and start >= next_free[duration]
            next_free[duration] = start + duration
            events.add(start + duration)
        return sorted(events)
    serial = observe([(0, 7), (7, 4), (11, 4)])
    both = observe([(0, 7), (0, 4), (4, 4), (8, 7)])
    assert serial == [0, 7, 11, 15]
    assert both == [0, 4, 7, 8, 15]
    return {'serial_schedule_minutes': serial, 'both_start_together_minutes': both}


if __name__ == '__main__':
    for number, check in ((382, cylinder), (383, cards), (384, hourglasses)):
        result = {'status': 'passed', **check()}
        Path(__file__).with_name(f'prep-{number}-1118b-verification.json').write_text(
            json.dumps(result, indent=2) + '\n', encoding='utf8')
        print(number, result)
