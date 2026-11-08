"""Trusted models, independent list/deque/string/arithmetic expectations."""
from __future__ import annotations

import itertools
import json
import random
import runpy
from collections import deque
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
SOLUTIONS = BANK / "solutions"
remove_spaces = runpy.run_path(str(SOLUTIONS / "prep_303_remove_spaces_1108b20.py"))["remove_spaces"]
cursor_module = runpy.run_path(str(SOLUTIONS / "prep_304_cursor_stacks_1108b20.py"))
queue_module = runpy.run_path(str(SOLUTIONS / "prep_305_queue_stacks_1108b20.py"))
execute = runpy.run_path(str(SOLUTIONS / "prep_035_311_vm_1108b20.py"))["execute_listing"]


def cursor_oracle(operations):
    values, current, output = [], 0, []
    for operation in operations:
        name, *args = operation
        if name.startswith("insert_"):
            if not values:
                values.append(args[0])
            elif name == "insert_before":
                values.insert(current, args[0])
                current += 1
            else:
                values.insert(current + 1, args[0])
            result = None
        elif name.startswith("move_"):
            direction = -1 if name == "move_prev" else 1
            result = bool(values and 0 <= current + direction < len(values))
            if result:
                current += direction
        else:
            index = current + (-1 if name == "prev" else 1 if name == "next" else 0)
            if not values or not 0 <= index < len(values):
                output.append({"ok": False, "error": "empty_or_boundary"})
                continue
            result = values[index]
            if name == "delete":
                values.pop(current)
                current = max(0, min(current, len(values) - 1))
        output.append({"ok": True, "value": result})
    return output


def queue_oracle(operations):
    model, output = deque(), []
    for operation in operations:
        name, *args = operation
        if name == "enqueue":
            model.append(args[0])
            value = None
        elif name == "is_empty":
            value = not model
        elif not model:
            output.append({"ok": False, "error": "empty"})
            continue
        else:
            value = model.popleft() if name == "dequeue" else model[0]
        output.append({"ok": True, "value": value})
    return output


def counted_stack(stack_class):
    count = {"primitives": 0, "moves": 0}
    for name in ("empty", "top", "push", "pop"):
        original = getattr(stack_class, name)

        def wrapper(self, *args, _name=name, _method=original):
            count["primitives"] += 1
            result = _method(self, *args)
            if _name in ("push", "pop"):
                count["moves"] += 1
            return result

        setattr(stack_class, name, wrapper)
    return count


def main():
    spaces = 0
    for n in range(6):
        for letters in itertools.product("a \tא", repeat=n):
            text = "".join(letters)
            assert remove_spaces(text) == text.replace(" ", "")
            spaces += 1
    assert remove_spaces(" a\nb\u00a0 c ") == "a\nb\u00a0c"
    spaces += 1
    rng = random.Random(110820)
    choices = ["get", "prev", "next", "move_prev", "move_next",
               "insert_before", "insert_after", "delete"]
    operations = []
    for _ in range(5000):
        name = rng.choice(choices)
        operations.append([name, rng.randrange(-4, 5)] if name.startswith("insert_") else [name])
    count = counted_stack(cursor_module["_Stack"])
    cursor = cursor_module["CursorList"]()
    actual = []
    for name, *args in operations:
        before = count["primitives"]
        try:
            actual.append({"ok": True, "value": getattr(cursor, name)(*args)})
        except IndexError:
            actual.append({"ok": False, "error": "empty_or_boundary"})
        assert count["primitives"] - before <= 8
    assert actual == cursor_oracle(operations)
    queue_ops = []
    for _ in range(5000):
        name = rng.choice(["enqueue", "dequeue", "peek", "is_empty"])
        queue_ops.append([name, rng.randrange(-4, 5)] if name == "enqueue" else [name])
    count = counted_stack(queue_module["_Stack"])
    assert queue_module["queue_trace"](queue_ops) == queue_oracle(queue_ops)
    enqueues = sum(op[0] == "enqueue" for op in queue_ops)
    assert count["moves"] <= 4 * enqueues
    multiply = (SOLUTIONS / "prep_035_register_unit_1108b20.txt").read_text("utf-8")
    division = (SOLUTIONS / "prep_311_exact_division_1108b20.txt").read_text("utf-8")
    multiply_cases = 0
    for a, b, result, temp in itertools.product(range(13), range(13), range(4), range(4)):
        final, _ = execute(multiply, {"A": a, "B": b, "R2": result, "T": temp}, "named")
        assert final["R2"] == a * b and final["A"] == a
        multiply_cases += 1
    divide_cases = 0
    for divisor in range(1, 21):
        for quotient in range(21):
            final, _ = execute(division, {"A": divisor * quotient, "B": divisor,
                                        "C": 0, "T": 0, "S": 0, "U": 0}, "flags")
            assert final["C"] == quotient and final["A"] == 0 and final["B"] == divisor
            divide_cases += 1
    rejected = 0
    for text, registers, branch in [("DEC A", {"A": 0}, "flags"),
                                    ("JNZ END\nEND:", {"A": 1}, "flags"),
                                    ("INC A\nJNZ END\nEND:\nJNZ END", {"A": 1}, "flags"),
                                    ("CLEAR A", {"A": 3}, "named")]:
        try:
            execute(text, registers, branch, max_steps=20)
            raise AssertionError("invalid instruction accepted")
        except ValueError:
            rejected += 1
    buckets = 0
    for maximum in range(7, 49):
        for bound in range(2, min(10, maximum) + 1):
            limit = maximum - maximum % bound
            counts = [sum(draw % bound == bucket for draw in range(limit)) for bucket in range(bound)]
            assert len(set(counts)) == 1 and counts[0] > 0
            buckets += 1
    report = {
        "status": "passed", "scope": "Trusted Python models and educational unit-opcode interpreter, not native assembly.",
        "PREP-303": {"string_cases": spaces, "oracle": "replace used only in the independent checker"},
        "PREP-304": {"operations": 5000, "oracle": "ordinary list and cursor index",
                     "max_stack_primitives_per_operation": 8},
        "PREP-305": {"operations": 5000, "oracle": "collections.deque",
                     "push_pop_total_at_most_four_per_enqueued_value": True},
        "PREP-035": {"listing_cases": multiply_cases, "dirty_result_and_temp": True,
                     "named_register_branches": True, "CLEAR_not_permitted": True},
        "PREP-311": {"listing_cases": divide_cases, "exact_positive_divisor_domain": True,
                     "previous_result_flag_branches": True, "quotient_and_preserved_divisor": True},
        "invalid_opcode_or_branch_cases": rejected,
        "PREP-022": {"equal_bucket_model_domains": buckets,
                     "native_C_and_PRNG_scope": "Separate native report; no statistical proof about C rand."},
        "PREP-309": {"native_Java": "Separate actual javac/java report, not a Python replacement."},
    }
    (BANK / "checks/1108b20-software-verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for number in (303, 304, 305, 35, 311, 22):
        result = {"status": "passed", "scope": report[f"PREP-{number:03d}"],
                  "batch_report": "checks/1108b20-software-verification.json"}
        (BANK / f"checks/prep-{number:03d}-1108b20-verification.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
