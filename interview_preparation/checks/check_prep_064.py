"""Exhaustive gate-model checks against an independent arithmetic oracle."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prep064", ROOT / "solutions/prep_064_three_bit_up_down.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def oracle(q, inc, dec, reset=False):
    return 0 if reset else (q + inc - dec) % 8


def main():
    controls = tuple(itertools.product((0, 1), repeat=2))
    transitions = reset_transitions = 0
    rows = []
    for q in range(8):
        row = [q]
        for inc, dec in controls:
            actual = model.next_q(q, inc, dec)
            assert actual == oracle(q, inc, dec)
            row.append(actual)
            transitions += 1
            assert model.next_q(q, inc, dec, reset=True) == 0
            reset_transitions += 1
        rows.append(row)
    streams = edges = 0
    for initial in range(8):
        for length in range(7):
            for sequence in itertools.product(controls, repeat=length):
                actual = expected = initial
                for inc, dec in sequence:
                    actual = model.next_q(actual, inc, dec)
                    expected = oracle(expected, inc, dec)
                    assert actual == expected
                    edges += 1
                streams += 1
    reset_streams = reset_edges = 0
    actions = tuple(itertools.product((0, 1), repeat=3))
    for initial in range(8):
        for sequence in itertools.product(actions, repeat=4):
            actual = expected = initial
            for inc, dec, reset in sequence:
                actual = model.next_q(actual, inc, dec, reset=bool(reset))
                expected = oracle(expected, inc, dec, reset)
                assert actual == expected
                reset_edges += 1
            reset_streams += 1
    report = {
        "question_id":"PREP-064", "checked_on":"2026-10-21", "status":"passed_python_model",
        "state_control_transitions":transitions, "reset_priority_transitions":reset_transitions,
        "all_streams_lengths_0_through_6_from_eight_states":streams, "stream_edges":edges,
        "all_length_four_control_reset_streams_from_eight_states":reset_streams, "reset_stream_edges":reset_edges,
        "table_columns":["q", "inc=0 dec=0", "inc=0 dec=1", "inc=1 dec=0", "inc=1 dec=1"],
        "transition_table":rows,
        "oracle":"Independent integer +1/-1/hold modulo eight; reset oracle always zero.",
        "scope":"Python functional model only; no HDL compilation/simulation, synthesis, physical timing or independent professional approval.",
    }
    (ROOT / "checks/prep-064-verification.json").write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
