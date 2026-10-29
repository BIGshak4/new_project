"""Independent arithmetic/prefix oracles for all 265 basic hardware variants."""

import itertools
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads(
    (ROOT / "backend/seeds/duel_quiz_batches/hardware_basic.checks.json").read_text(encoding="utf-8")
)


def seq(values, width=None):
    return ", ".join(format(x, f"0{width}b") if width else str(x) for x in values)


def reference(case):
    p, method = case["inputs"], case["method"]
    if method in {"truth", "truth_count", "gate_identity"}:
        functions = {
            "and": lambda a, b, c: min(a, b),
            "or": lambda a, b, c: max(a, b),
            "nand": lambda a, b, c: 1 - min(a, b),
            "nor": lambda a, b, c: 1 - max(a, b),
            "xnor": lambda a, b, c: 1 - abs(a - b),
            "majority": lambda a, b, c: sorted([a, b, c])[1],
            "factor": lambda a, b, c: min(a, max(b, c)),
        }
        if method == "gate_identity":
            return {
                "and": "AND",
                "or": "OR",
                "nand": "NAND",
                "nor": "NOR",
                "xnor": "XNOR",
                "majority": "(A AND B) OR (A AND C) OR (B AND C)",
                "factor": "A AND (B OR C)",
            }[p["operation"]]
        vals = [functions[p["operation"]](*(row + [0] if len(row) == 2 else row)) for row in p["rows"]]
        return str(sum(vals)) if method == "truth_count" else seq(vals)
    if method == "invert":
        return format((2 ** len(p["word"]) - 1) - int(p["word"], 2), f"0{len(p['word'])}b")
    if method == "absorb":
        return seq([a for a, _ in p["rows"]])
    if method == "shift_left":
        return format((p["value"] * 2 ** p["shift"]) % 2 ** p["width"], f"0{p['width']}b")
    if method == "mask":
        return format((p["value"] // 2 ** p["bit"] % 2) * 2 ** p["bit"], "08b")
    if method == "setclear":
        weights = [(p["value"] // 2**i % 2) if i != p["bit"] else p["target"] for i in range(8)]
        return format(sum(x * 2**i for i, x in enumerate(weights)), "08b")
    if method == "parity":
        return seq([int(word, 2).bit_count() % 2 for word in p["words"]])
    if method == "pipe":
        width = len(p["initial"])
        history = list(reversed(p["initial"])) + p["inputs"]
        words = [
            int("".join(map(str, reversed(history[i + 1 : i + 1 + width]))), 2)
            for i in range(len(p["inputs"]))
        ]
        return seq(words, width)
    if method == "toggle":
        return seq([(p["initial"] + sum(p["inputs"][: i + 1])) % 2 for i in range(len(p["inputs"]))])
    if method == "reset_register":
        return format(0 if p["rst"] == p["active"] else p["data"] if p["enable"] else p["initial"], "02b")
    if method == "sync_async":
        return seq([0 if p["edge"] and p["reset"] else p["initial"], 0 if p["reset"] else p["initial"]], 2)
    if method in {"rise", "pairs11", "run11"}:
        prior = [p["initial"]] + p["inputs"][:-1]
        return seq(
            [
                int(x > old) if method == "rise" else int(bool(x and old))
                for old, x in zip(prior, p["inputs"], strict=True)
            ]
        )
    if method == "sticky":
        return seq([int(any(p["inputs"][: i + 1])) for i in range(len(p["inputs"]))])
    if method == "stream_parity":
        return seq([(p["initial"] + sum(p["inputs"][: i + 1])) % 2 for i in range(len(p["inputs"]))])
    if method == "vending":
        return seq([int(x == 1 and sum(p["inputs"][: i + 1]) % 2 == 0) for i, x in enumerate(p["inputs"])])
    if method == "statebits":
        bits = math.ceil(math.log2(p["states"]))
        return seq([bits, 2**bits - p["states"]])
    if method == "cycle":
        return f"S{(p['initial'] + p['edges']) % p['states']}"
    if method == "to_binary":
        return format(p["value"], f"0{p['width']}b")
    if method == "signed_pair":
        unsigned = int(p["word"], 2)
        signed = -int(p["word"][0]) * 2 ** (len(p["word"]) - 1) + int(p["word"][1:], 2)
        return seq([unsigned, signed])
    if method == "signextend":
        signed = int(p["word"], 2) - 2 ** len(p["word"])
        return format(signed % 2 ** p["width"], f"0{p['width']}b")
    if method == "onehot":
        return next(w for w in p["words"] if int(w, 2) > 0 and math.log2(int(w, 2)).is_integer())
    if method == "fulladder":
        return format(sum([p["a"], p["b"], p["cin"]]), "02b")
    if method == "rightshift":
        u = int(p["word"], 2)
        signed = u - (256 if u >= 128 else 0)
        return seq([u // 2, (signed // 2) % 256], 8)
    if method == "enabled_counter":
        return seq([(p["initial"] + sum(p["inputs"][: i + 1])) % 8 for i in range(len(p["inputs"]))], 3)
    if method == "down":
        return format((p["initial"] - p["edges"]) % 2 ** p["width"], f"0{p['width']}b")
    if method == "counter_bit":
        return seq(
            [int(format((p["initial"] + k) % 8, "03b")[-1 - p["bit"]]) for k in range(1, p["edges"] + 1)]
        )
    if method == "busy":
        transitions = {
            (0, 0, 0): 0,
            (0, 0, 1): 0,
            (0, 1, 0): 1,
            (0, 1, 1): 1,
            (1, 0, 0): 1,
            (1, 1, 0): 1,
            (1, 0, 1): 0,
            (1, 1, 1): 0,
        }
        state, out = p["initial"], []
        for request, done in p["inputs"]:
            state = transitions[state, request, done]
            out.append(state)
        return seq(out)
    if method == "onehot_width":
        return str(p["states"])
    if method == "reachability":
        # Any reachable node has a simple path shorter than the node count.
        reached = {p["initial"]}
        for length in range(1, len(p["graph"])):
            for word in itertools.product((0, 1), repeat=length):
                state = p["initial"]
                for bit in word:
                    state = p["graph"][state][bit]
                reached.add(state)
        return ", ".join(sorted(reached))
    if method == "priority":
        return seq([{(0, 0): "S", (0, 1): "B", (1, 0): "A", (1, 1): "A"}[tuple(row)] for row in p["rows"]])
    if method == "recovery":
        return format((p["recovery"] + p["edges"] - 1) % 3, "02b")
    if method == "integer_parity":
        return seq([int(word[-1]) for word in p["words"]])
    if method == "inversion_chain":
        return seq([x if p["count"] % 2 == 0 else 1 - x for x in [0, 1]])
    if method == "enable_mux":
        # The four possible Q/data values are fully defined, even for hold.
        return f"D0=Q, D1=data; Q={(p['initial'], p['data'])[p['enable']]}"
    if method == "uninitialized_d":
        return f"Unspecified; {p['data']}"
    if method == "output_dependency":
        return p["classification"]  # separately reviewed Boolean output definitions
    if method == "absorption_concept":
        return {
            "identity": "A",
            "fixed_one": "Y stays 1",
            "inverse_zero": "A=0; B may be 0 or 1",
            "remove_branch": "The A AND B branch",
        }[p["case"]]
    if method == "mux_function":

        def evaluate(expr, env):
            if expr in ("0", "1"):
                return int(expr)
            if expr.startswith("NOT "):
                return 1 - env[expr[4:]]
            if " AND " in expr:
                return min(env[c] for c in expr.split(" AND "))
            if " OR " in expr:
                return max(env[c] for c in expr.split(" OR "))
            return env[expr]

        for values in itertools.product((0, 1), repeat=4):
            env = dict(zip("ABCD", values, strict=True))
            assert evaluate((p["d0"], p["d1"])[evaluate(p["selector"], env)], env) == evaluate(
                p["target"], env
            )
        return f"D0={p['d0']}, D1={p['d1']}"
    raise AssertionError(f"Uncovered method {method}")


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["key"])
def test_basic_variant_against_independent_oracle(case):
    assert reference(case) == case["expected"]["en"]
