"""Exact symmetry-reduced safety search and individual-memory executions."""
from collections import deque
import importlib.util
import json
from pathlib import Path
import random
import sys

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prisoners101", BANK / "solutions/prep_054_101_prisoners_variant.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def exhaustive(known):
    cap = 1 if known else 2
    starts = [(0, 0)] if known else [(s,d) for s in (0,1) for d in (0,1)]
    states_total = transitions = terminals = 0
    for initial_signal, initial_dummy in starts:
        histogram = (100,) + (0,)*cap
        start = (histogram, initial_signal, 0, initial_dummy)
        seen, queue = {start}, deque([start])
        while queue:
            hist, signal, count, dummy = queue.popleft()
            emitted = sum(j*n for j,n in enumerate(hist))
            assert sum(hist) == 100 and count+signal == emitted+initial_signal
            if count == 100*cap:
                assert hist[0] == 0
                terminals += 1
                continue
            assert count < 100*cap
            if not signal:
                assert sum(hist[:-1]) > 0
            successors = [(hist, 0, count+1, dummy)] if signal else [(hist, signal, count, 1-dummy)]
            for sent, population in enumerate(hist):
                if not population:
                    continue
                if not signal and sent < cap:
                    h = list(hist)
                    h[sent] -= 1
                    h[sent+1] += 1
                    successors.append((tuple(h), 1, count, dummy))
                else:
                    successors.append((hist, signal, count, 1-dummy))
            for successor in successors:
                transitions += 1
                # Each branch changes exactly one physical light.
                _, next_signal, _, next_dummy = successor
                assert int(signal!=next_signal)+int(dummy!=next_dummy)==1
                if successor not in seen:
                    seen.add(successor)
                    queue.append(successor)
        states_total += len(seen)
    return {"reachable_states": states_total, "transitions": transitions, "safe_terminal_states": terminals}


def samples(known):
    settings = [(False,False)] if known else [(s,d) for s in (False,True) for d in (False,True)]
    runs, maximum = 0, 0
    for signal, dummy in settings:
        for seed in range(100):
            rng = random.Random(seed)
            protocol = module.Protocol101(known_both_off=known, signal=signal, dummy=dummy)
            visited = set()
            emitted = 0
            for ticks in range(1, 200001):
                p = rng.randrange(101)
                before = (protocol.signal, protocol.dummy, protocol.sent[p])
                visited.add(p)
                _, done = protocol.visit(p)
                emitted += protocol.sent[p]-before[2]
                assert int(before[0]!=protocol.signal)+int(before[1]!=protocol.dummy)==1
                assert protocol.count+int(protocol.signal) == emitted+int(signal)
                assert protocol.sent[p] <= protocol.allowance
                if done:
                    assert len(visited) == 101
                    runs += 1
                    maximum = max(maximum, ticks)
                    break
            else:
                raise AssertionError("Seeded test exceeded its finite test cap")
    return {"runs": runs, "largest_test_visit_count": maximum}


def run():
    result = {"question_id": "PREP-054", "variant": "101 prisoners, one-or-both lights must change", "status": "passed"}
    for known in (True, False):
        name = "known_both_off" if known else "unknown_initial"
        result[name] = {"threshold": 100 if known else 200,
                        **exhaustive(known), **samples(known)}
    result["limits"] = "Exhaustive reachable aggregate safety search is exact under contributor symmetry. Finite individual simulations do not establish termination for every schedule. The written termination proof separately assumes fair repeated visitation. No physical experiment or human expert approval."
    (BANK / "checks/prep-054-101-verification.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
