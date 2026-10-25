"""Independent postfix parsing and four-op ISA checks for PREP-123/125."""
from __future__ import annotations

import importlib.util
import itertools
import random
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POSTFIX = load("prep_123_postfix_stack")
MACHINE = load("prep_125_primitive_register_machine")


def recursive_postfix_oracle(tokens):
    """Parse from the right recursively; do not simulate the solution stack."""
    def parse(end):
        if end < 0:
            raise ValueError("missing operand")
        token = tokens[end]
        if type(token) is int:
            return token, end - 1
        if token not in ("+", "-", "*"):
            raise ValueError("invalid token")
        right, end = parse(end - 1)
        left, end = parse(end)
        value = left + right if token == "+" else left - right if token == "-" else left * right
        return value, end

    result, remaining = parse(len(tokens) - 1)
    if remaining != -1:
        raise ValueError("unused prefix")
    return result


def check_postfix_cases():
    cases = valid = invalid = 0
    for length in range(8):
        for tokens in itertools.product((-1, 2, "+", "-", "*"), repeat=length):
            before = tuple(tokens)
            try:
                expected = recursive_postfix_oracle(tokens)
            except ValueError:
                with pytest.raises(ValueError):
                    POSTFIX.evaluate_postfix(tokens)
                invalid += 1
            else:
                assert POSTFIX.evaluate_postfix(tokens) == expected
                valid += 1
            assert tokens == before
            cases += 1
    assert POSTFIX.evaluate_postfix([3, 2, "+", 5, "+", 2, "*"]) == 20
    assert POSTFIX.evaluate_postfix([3, 2, "-"]) == 1
    assert POSTFIX.evaluate_postfix([2, 3, "-"]) == -1
    invalid_extra = (None, "3 2 +", [True], [1.5], ["3"], ["/"], [1, 0, "/"], [[]])
    for tokens in invalid_extra:
        with pytest.raises(ValueError):
            POSTFIX.evaluate_postfix(tokens)
    # Negative and large exact integers are values, not unary operator tokens.
    value = 10**100
    assert POSTFIX.evaluate_postfix([value, -3, "*", 2, "-"]) == -3 * value - 2
    return {"exhaustive_token_streams": cases, "valid_streams": valid,
            "invalid_streams": invalid, "additional_invalid_inputs": len(invalid_extra)}


def check_machine_cases():
    programs = {name: MACHINE.assemble(source) for name, source in MACHINE.supplied_programs().items()}
    assert all(opcode in {"INC", "DEC", "JNZ", "HALT"}
               for instructions, _ in programs.values() for opcode, _ in instructions)
    cases = maximum_steps = 0
    pairs = list(itertools.product(range(33), repeat=2))
    rng = random.Random(125)
    pairs += [(rng.randrange(65), rng.randrange(65)) for _ in range(100)]
    pairs += [(0, 1000), (1000, 0), (1, 999), (999, 1)]
    for a, b in pairs:
        product = MACHINE.execute(programs["multiply"], a, b)
        difference = MACHINE.execute(programs["absolute_difference"], a, b)
        assert product["registers"]["C"] == a * b
        assert product["registers"]["A"] == a
        assert product["registers"]["B"] == product["registers"]["D"] == 0
        assert product["steps"] == b * (17 * a + 13) + 5
        assert difference["registers"]["C"] == abs(a - b)
        assert difference["registers"]["A"] == difference["registers"]["B"] == 0
        assert all(value >= 0 for result in (product, difference) for value in result["registers"].values())
        assert product["registers"]["Z"] == difference["registers"]["Z"] == 1
        maximum_steps = max(maximum_steps, product["steps"], difference["steps"])
        cases += 2
    return {"exhaustive_grid_pairs": 33 * 33, "seeded_pairs": 100, "extra_boundary_pairs": 4,
            "program_executions": cases, "maximum_executed_instructions": maximum_steps}


def test_postfix_matches_recursive_parsing_oracle_and_rejects_malformed_streams():
    result = check_postfix_cases()
    assert result["exhaustive_token_streams"] == 97656
    assert result["valid_streams"] + result["invalid_streams"] == 97656


def test_both_actual_expanded_programs_match_arithmetic_oracles_and_halt():
    assert check_machine_cases()["program_executions"] == 2386


def test_jnz_uses_immediately_previous_instruction_result_and_has_no_register_argument():
    program = "INC A\nDEC B\nJNZ DONE\nINC C\nHALT\nDONE:\nHALT"
    assert MACHINE.execute(program, 0, 1)["registers"]["C"] == 1
    assert MACHINE.execute(program, 0, 2)["registers"]["C"] == 0
    with pytest.raises(ValueError, match="immediately"):
        MACHINE.execute("JNZ DONE\nDONE:\nHALT", 1, 1)
    with pytest.raises(ValueError, match="immediately"):
        MACHINE.execute("INC A\nJNZ NEXT\nHALT\nNEXT:\nJNZ END\nEND:\nHALT", 0, 0)
    for source in ("MOV A B", "CMP A B", "JMP END\nEND:\nHALT", "JNZ A END\nEND:\nHALT", "INC AA", "INC A\nJNZ MISSING"):
        with pytest.raises(ValueError):
            MACHINE.assemble(source)


def test_machine_rejects_underflow_invalid_inputs_and_missing_termination():
    with pytest.raises(ValueError, match="DEC at zero"):
        MACHINE.execute("DEC A\nHALT", 0, 0)
    with pytest.raises(ValueError, match="fell off"):
        MACHINE.execute("INC A", 0, 0)
    with pytest.raises(TimeoutError):
        MACHINE.execute("LOOP:\nINC A\nJNZ LOOP", 0, 0, max_steps=10)
    for value in (-1, True, 0.5):
        with pytest.raises(ValueError):
            MACHINE.execute("HALT", value, 0)
