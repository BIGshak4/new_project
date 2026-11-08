"""An educational unit-instruction interpreter, not a physical CPU assembler."""


def execute_listing(text, initial, branch, max_steps=1000000):
    if branch not in ("named", "flags"):
        raise ValueError("choose named-register or previous-result branching")
    if any(type(v) is not int or v < 0 for v in initial.values()):
        raise ValueError("natural registers required")
    instructions, labels = [], {}
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.endswith(":"):
            label = line[:-1]
            if label in labels:
                raise ValueError("duplicate label")
            labels[label] = len(instructions)
        else:
            instructions.append(line.replace(",", " ").split())
    registers = dict(initial)
    pc = steps = 0
    flag = None
    increment, decrement = ("ADD", "SUM") if branch == "named" else ("INC", "DEC")
    while pc < len(instructions):
        if steps >= max_steps:
            raise TimeoutError("unit-instruction step limit")
        steps += 1
        opcode, *args = instructions[pc]
        pc += 1
        if opcode in (increment, decrement) and len(args) == 1 and args[0] in registers:
            reg = args[0]
            if opcode == decrement and registers[reg] == 0:
                raise ValueError("decrement at zero")
            registers[reg] += 1 if opcode == increment else -1
            flag = registers[reg] != 0
        elif opcode == "JNZ":
            if branch == "named" and len(args) == 2 and args[0] in registers:
                condition, label = registers[args[0]] != 0, args[1]
            elif branch == "flags" and len(args) == 1 and flag is not None:
                condition, label = flag, args[0]
            else:
                raise ValueError("invalid branch or stale flags")
            if label not in labels:
                raise ValueError("unknown label")
            if condition:
                pc = labels[label]
            flag = None
        else:
            raise ValueError("opcode not allowed in the chosen contract")
    return registers, steps
