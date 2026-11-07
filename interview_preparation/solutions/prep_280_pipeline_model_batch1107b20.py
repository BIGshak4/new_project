"""Stage-completion teaching schedule, not an ISA implementation.

An offered token is processed by stage1 during a slot and enters its result
register at that slot's ending edge. Stage5 completion is visible at edge5.
Each slot has one period; a global stall freezes the entire toy machine.
"""

def schedule(offers, stalls=(), stages=5):
    if type(stages) is not int or stages < 1:
        raise ValueError("positive stage count required")
    state = [None] * stages
    blocked = set(stalls)
    result = []
    for cycle, offered in enumerate(offers, 1):
        if cycle in blocked:
            if offered is not None:
                raise ValueError("no new token may be accepted during global stall")
            result.append((cycle, tuple(state), None))
        else:
            state = [offered] + state[:-1]
            result.append((cycle, tuple(state), state[-1]))
    return result


def ideal_cycles(instructions, stages=5):
    if type(instructions) is not int or instructions < 0 or type(stages) is not int or stages < 1:
        raise ValueError("nonnegative instruction count and positive stages required")
    return 0 if instructions == 0 else stages + instructions - 1
