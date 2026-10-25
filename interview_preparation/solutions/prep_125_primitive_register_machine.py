"""Interpreter for the educational four-instruction ISA, not real CPU assembly.

A..Z are unbounded natural-valued registers. A/B receive nonnegative inputs;
all others start at zero. DEC at zero is rejected. JNZ reads only the result
of the immediately preceding executed INC/DEC and never names a register.
The supplied programs use only these operations and labels, without macros.
"""
from pathlib import Path
from string import ascii_uppercase

OPS = {"INC", "DEC", "JNZ", "HALT"}


def assemble(source):
    instructions, labels = [], {}
    for raw in source.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.endswith(":"):
            label = line[:-1]
            if not label.isidentifier() or label in labels:
                raise ValueError("invalid or repeated label")
            labels[label] = len(instructions)
            continue
        parts = line.split()
        opcode = parts[0]
        if opcode not in OPS or len(parts) != (1 if opcode == "HALT" else 2):
            raise ValueError("only INC, DEC, JNZ and HALT with exact arity are allowed")
        operand = parts[1] if len(parts) == 2 else None
        if opcode in {"INC", "DEC"} and operand not in ascii_uppercase:
            raise ValueError("register must be A..Z")
        if opcode in {"INC", "DEC"} and len(operand) != 1:
            raise ValueError("register must be one letter")
        instructions.append((opcode, operand))
    if not instructions:
        raise ValueError("empty program")
    if any(op == "JNZ" and arg not in labels for op, arg in instructions):
        raise ValueError("unknown branch label")
    return tuple(instructions), labels


def execute(program, a, b, *, max_steps=2_000_000, trace=False):
    if any(type(value) is not int or value < 0 for value in (a, b)):
        raise ValueError("A and B must be nonnegative integers")
    instructions, labels = assemble(program) if isinstance(program, str) else program
    registers = dict.fromkeys(ascii_uppercase, 0)
    registers.update(A=a, B=b)
    pc = steps = 0
    previous_opcode = last_result = None
    history = [] if trace else None
    while 0 <= pc < len(instructions):
        if steps >= max_steps:
            raise TimeoutError("instruction bound reached")
        opcode, operand = instructions[pc]
        steps += 1
        if history is not None:
            history.append((pc, opcode, operand, last_result, previous_opcode))
        if opcode == "HALT":
            return {"registers": registers, "steps": steps, "trace": history}
        if opcode == "JNZ":
            if previous_opcode not in {"INC", "DEC"}:
                raise ValueError("JNZ must immediately follow an executed INC or DEC")
            pc = labels[operand] if last_result != 0 else pc + 1
            previous_opcode, last_result = "JNZ", None
            continue
        if opcode == "DEC" and registers[operand] == 0:
            raise ValueError("DEC at zero is outside this natural-register contract")
        registers[operand] += 1 if opcode == "INC" else -1
        previous_opcode, last_result = opcode, registers[operand]
        pc += 1
    raise ValueError("execution fell off the program without HALT")


def supplied_programs():
    folder = Path(__file__).resolve().parent
    return {
        "multiply": (folder / "prep_125_primitive_multiply.asm").read_text("utf-8"),
        "absolute_difference": (folder / "prep_125_primitive_absolute_difference.asm").read_text("utf-8"),
    }
