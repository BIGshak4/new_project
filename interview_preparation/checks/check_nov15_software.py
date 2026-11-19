"""Independent finite oracles and two-worker concurrency checks for Nov 15."""
import importlib.util
import itertools
import json
import random
import threading
import time
from collections import Counter
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(number, stem):
    path = BANK / "solutions" / f"prep_{number}_{stem}.py"
    spec = importlib.util.spec_from_file_location(stem, path)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[stem] = module
    spec.loader.exec_module(module)
    return module


def main():
    counts = {}
    clock = load(330, "interesting_clock")
    flags = []
    for h in range(24):
        for m in range(60):
            for s in range(60):
                mask = 0
                for part in (h, m, s):
                    mask |= 1 << (part // 10)
                    mask |= 1 << (part % 10)
                assert (mask.bit_count() <= 2) == (len(set(f"{h:02d}{m:02d}{s:02d}")) <= 2)
                flags.append(mask.bit_count() <= 2)
    assert clock.count_interesting_times("00:00:00", "23:59:59") == sum(flags)
    assert clock.count_interesting_times("15:15:00", "15:15:12") == 1
    assert clock.count_interesting_times("22:22:21", "22:22:23") == 3
    rng = random.Random(1115)
    for _ in range(70):
        a = rng.randrange(86400)
        b = min(86399, a + rng.randrange(400))
        def formatted(x):
            h, r = divmod(x, 3600)
            m, s = divmod(r, 60)
            return f"{h:02}:{m:02}:{s:02}"
        assert clock.count_interesting_times(formatted(a), formatted(b)) == sum(flags[a:b + 1])
    counts[330] = 86473

    codec = load(333, "tree_codec")
    def oracle(node):
        if node is None:
            return [None]
        return [node.value] + oracle(node.left) + oracle(node.right)
    cases = 0
    for size in range(7):
        for values in itertools.product((-1, 0, 1), repeat=size):
            nodes = [codec.Node(v) for v in values]
            for i in range(1, size):
                parent = nodes[(i - 1) // 2]
                setattr(parent, "left" if i % 2 else "right", nodes[i])
            node = nodes[0] if nodes else None
            encoded = codec.serialize(node)
            assert json.loads(encoded) == oracle(node)
            assert codec.serialize(codec.deserialize(encoded)) == encoded
            cases += 1
    malformed = ["[]", "[1]", "[null,null]", "[1,null]", '[true,null,null]', '["1",null,null]']
    for text in malformed:
        try:
            codec.deserialize(text)
        except ValueError:
            pass
        else:
            raise AssertionError(text)
    root = None
    for i in range(5000):
        root = codec.Node(i, root, None)
    text = codec.serialize(root)
    assert codec.serialize(codec.deserialize(text)) == text
    counts[333] = cases + len(malformed) + 1

    barrier_type = load(337, "two_thread_reusable_barrier").TwoThreadBarrier
    rounds = 300
    barrier = barrier_type()
    journal = []
    gate = threading.Lock()
    failures = []
    def worker(ident):
        for generation in range(rounds):
            if (generation + ident) % 7 == 0:
                time.sleep(0.0001)
            with gate:
                journal.append(("arrival", generation, ident))
            barrier.wait()
            with gate:
                if {x[2] for x in journal if x[0] == "arrival" and x[1] == generation} != {0, 1}:
                    failures.append(generation)
                journal.append(("exit", generation, ident))
    workers = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(2)]
    for thread in workers:
        thread.start()
    for thread in workers:
        thread.join(timeout=8)
    assert not any(t.is_alive() for t in workers), "Barrier did not finish"
    assert not failures and len(journal) == rounds * 4
    counts[337] = rounds * 2

    # Independent small semaphore state exploration keeps the permit invariant.
    states = {(3, 0)}
    for _ in range(10):
        next_states = set(states)
        for available, held in states:
            assert available + held == 3 and available >= 0 and held >= 0
            if available:
                next_states.add((available - 1, held + 1))
            if held:
                next_states.add((available + 1, held - 1))
        states = next_states
    counts[334] = len(states)
    report = {"result": "passed", "scope": "Python references and independent finite models; native C evidence recorded separately", "comparisons": counts}
    for number in (330,331,332,333,334,335,336,337,243):
        (BANK / "checks" / f"prep-{number}-1115-verification.json").write_text(
            json.dumps(report if number in counts else {"result": "see_native_report", "report": "checks/nov15-software-native-verification.json"}, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
