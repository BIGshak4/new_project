"""Independent serial-memory oracle across latencies, stalls and arbitration."""

import importlib.util
import itertools
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "ctrl139", BANK / "solutions/prep_139_handshake_memory_controller.py"
)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def exercise(requests, latency, command_stalls, response_stalls):
    controller = model.Controller()
    oracle_memory = {0: 7, 1: 9}
    device_memory = dict(oracle_memory)
    expected = []
    responses = []
    index = issued = tick = 0
    due = None
    op = None
    issue_wait = response_wait = 0
    previous_command = previous_response = None
    while index < len(requests) or controller.state != "IDLE":
        assert tick < 500
        request = requests[index] if index < len(requests) else None
        r = request[1:] if request and request[0] == "R" else None
        w = request[1:] if request and request[0] == "W" else None
        ready = controller.state == "ISSUE" and issue_wait >= command_stalls
        if controller.state == "ISSUE" and ready:
            assert due is None
            op = controller.pending
            due = tick + latency
            issued += 1
        completion = None
        if due == tick:
            if op[0] == "W":
                device_memory[op[1]] = op[2]
                completion = ("W", None)
            else:
                completion = ("R", device_memory[op[1]])
            due = None
        take_response = controller.state == "RESP" and response_wait >= response_stalls
        old_state = controller.state
        out = controller.step(r, w, command_ready=ready, completion=completion, response_ready=take_response)
        if previous_command is not None:
            assert out["command"] == previous_command
        if previous_response is not None:
            assert out["response"] == previous_response
        previous_command = out["command"] if out["command"] and not ready else None
        previous_response = out["response"] if out["response"] and not take_response else None
        if out["accepted"] is not None:
            kind, address, data = out["accepted"]
            if kind == "W":
                oracle_memory[address] = data
                expected.append(("W", None))
            else:
                expected.append(("R", oracle_memory[address]))
            index += 1
        if out["response"] is not None and take_response:
            responses.append(out["response"])
        assert not (out["read_ready"] and out["write_ready"])
        if old_state != "IDLE":
            assert out["accepted"] is None
        issue_wait = issue_wait + 1 if old_state == "ISSUE" and not ready else 0
        response_wait = response_wait + 1 if old_state == "RESP" and not take_response else 0
        tick += 1
    assert responses == expected
    assert device_memory == oracle_memory
    assert issued == len(requests)
    return tick


def run_checks():
    alphabet = [("R", 0, None), ("R", 1, None), ("W", 0, 0), ("W", 0, 1), ("W", 1, 1)]
    traces = cycles = 0
    for length in range(5):
        for requests in itertools.product(alphabet, repeat=length):
            for latency, issue_stall, response_stall in itertools.product((0, 1, 3), (0, 2), (0, 2)):
                cycles += exercise(requests, latency, issue_stall, response_stall)
                traces += 1
    controller = model.Controller()
    winners = []
    for _ in range(8):
        out = controller.step((0, None), (1, 3))
        winners.append(out["accepted"][0])
        assert not (out["read_ready"] and out["write_ready"])
        op = controller.pending[0]
        controller.step(command_ready=True, completion=(op, 7 if op == "R" else None))
        controller.step(response_ready=True)
    assert winners == ["R", "W"] * 4
    rejected = 0
    for state, ready, done in (
        ("IDLE", False, ("R", 0)),
        ("ISSUE", False, ("R", 0)),
        ("WAIT", False, ("W", None)),
        ("RESP", False, ("R", 0)),
    ):
        bad = model.Controller()
        bad.state, bad.pending = state, ("R", 0, None)
        try:
            bad.step(command_ready=ready, completion=done)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(state)
    return {
        "question_id": "PREP-139",
        "status": "passed",
        "exhaustive_request_sequences": 781,
        "latency_stall_configurations": 12,
        "executed_traces": traces,
        "cycle_steps": cycles,
        "simultaneous_port_arbitrations": len(winners),
        "malformed_completions_rejected": rejected,
        "scope": "Executed Python handshake/state model against independent sequential-memory results. Includes zero-cycle completion, command/response stalls and round-robin ties. No RTL, CDC, physical timing or unlimited-input buffering claim.",
    }


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-139-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))
