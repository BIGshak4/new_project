"""Independent bounded checks for the three new interface/observation problems."""
import importlib.util
import itertools
import json
import random
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOLUTIONS = HERE.parent / 'solutions'


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('.', '_'), SOLUTIONS / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_group(ident):
    count = 0
    if ident == 'PREP-201':
        model = load('prep_201_circular_room_lamps.py')

        class Rooms:
            def __init__(self, lamps, start):
                self.lamps = list(lamps)
                self.position = start
                self.moves = 0

            def move_clockwise(self):
                self.position = (self.position + 1) % len(self.lamps)
                self.moves += 1

            def move_counterclockwise(self):
                self.position = (self.position - 1) % len(self.lamps)
                self.moves += 1

            def lamp_is_on(self):
                return self.lamps[self.position]

            def set_lamp(self, value):
                self.lamps[self.position] = value

        for n in range(1, 11):
            for lamps in itertools.product((False, True), repeat=n):
                for start in range(n):
                    room = Rooms(lamps, start)
                    assert model.count_rooms(room) == n
                    assert room.position == start and room.moves <= n*(n+1)
                    count += 1
        for n in (1, 2, 11, 31, 80):
            room = Rooms([True]*n, 0)
            assert model.count_rooms(room) == n and room.moves == n*(n+1)
            count += 1
        scope = 'All 2,046 lamp configurations at sizes 1..10 and every start, plus exact all-on worst-case movement; simulator has identities, algorithm uses only physical-room interface.'
    elif ident == 'PREP-208':
        model = load('prep_208_task_snapshot_barrier.py')
        # Every permutation checks every possible snapshot before and after each
        # completion against independent finite set inclusion, including future IDs.
        for n in range(8):
            for order in itertools.permutations(range(1, n+1)):
                barrier = model.SnapshotBarrier()
                targets = [barrier.press()]
                for _ in range(n):
                    barrier.accept(); targets.append(barrier.press())
                done = set()
                for target in targets:
                    assert barrier.ready(target) == (set(range(1, target+1)) <= done)
                    count += 1
                for task in order:
                    barrier.complete(task); done.add(task)
                    for target in targets:
                        assert barrier.ready(target) == (set(range(1, target+1)) <= done)
                        count += 1
        barrier = model.SnapshotBarrier()
        a = barrier.accept(); target = barrier.press(); b = barrier.accept()
        barrier.complete(b)
        assert not barrier.ready(target) and not barrier.wait(target, timeout=0)
        barrier.complete(a)
        assert barrier.ready(target) and barrier.wait(target, timeout=0); count += 1
        scope = 'All completion permutations for 0..7 accepted tasks and every prefix target, checked with set inclusion, plus explicit later-task-finishes-first counterexample; lock serialization is a declared event model, not a concurrent stress test.'
    elif ident == 'PREP-209':
        model = load('prep_209_packet_residence_monitor.py')
        rng = random.Random(20261031)
        for _ in range(500):
            monitor = model.ResidenceMonitor()
            active = {}; completed = []; history = []
            clock = 0; next_id = 0
            for _ in range(40):
                clock += rng.randrange(4)
                if not active or rng.randrange(3):
                    next_id += 1
                    monitor.arrive(next_id, clock); active[next_id] = clock
                else:
                    packet = rng.choice(list(active))
                    start = active.pop(packet)
                    monitor.depart(packet, clock)
                    completed.append(clock-start); history.append((start, clock))
                clock += rng.randrange(3)
                result = monitor.query(clock)
                expected = Fraction(sum(completed), len(completed)) if completed else None
                ages = [clock-start for start in active.values()]
                assert result['completed_average'] == expected
                assert result['pending_average_age'] == (Fraction(sum(ages), len(ages)) if ages else None)
                # Independent sum of clipped packet intervals, not occupancy recurrence.
                assert result['occupancy_area'] == sum(end-start for start, end in history) + sum(ages)
                count += 1
        # Same anonymous arrival/departure observations, different exact completed mean.
        first = model.ResidenceMonitor(); second = model.ResidenceMonitor()
        for monitor in (first, second):
            monitor.arrive('old', 0); monitor.arrive('new', 9)
        first.depart('old', 10); second.depart('new', 10)
        a, b = first.query(10), second.query(10)
        assert a['completed_average'] == 10 and b['completed_average'] == 1
        assert a['occupancy_area'] == b['occupancy_area'] == 11
        assert a['pending_count'] == b['pending_count'] == 1; count += 1
        scope = '20,000 event/query pairs against explicit packet lifetimes and ages, plus indistinguishable anonymous event traces with completed means 10 versus 1. No physical traffic or stable-limit experiment.'
    else:
        raise ValueError(ident)
    return {'question_id': ident, 'passed': True, 'cases': count, 'scope': scope, 'professional_review': 'pending'}


def main():
    results = [run_group(ident) for ident in ('PREP-201', 'PREP-208', 'PREP-209')]
    for result in results:
        (HERE/f'{result["question_id"].lower()}-verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
