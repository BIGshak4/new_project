"""Eight natural-number registers; end of listing ends this abstract program."""
from pathlib import Path


def execute(a, b, source=None, limit=10_000_000, scratch=(0, 0, 0, 0, 0, 0)):
    if type(a) is not int or type(b) is not int or min(a, b) < 0:
        raise ValueError('Nonnegative integer inputs required')
    if source is None:
        source = Path(__file__).with_name('prep_125_eight_register_product_batch110.asm').read_text('utf-8')
    program, labels = [], {}
    for line in source.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.endswith(':'):
            labels[line[:-1]] = len(program)
        else:
            op, arg = line.split()
            if op not in ('INC', 'DEC', 'BNZ') or (op != 'BNZ' and arg not in {f'R{i}' for i in range(8)}):
                raise ValueError('Forbidden instruction/register')
            program.append((op, arg))
    if len(scratch) != 6 or any(type(v) is not int or v < 0 for v in scratch):
        raise ValueError('Six nonnegative scratch values required')
    registers = [a, b, *scratch]
    pc = steps = 0; previous = None
    while pc < len(program):
        if steps >= limit:
            raise RuntimeError('Instruction limit exceeded')
        op, arg = program[pc]; pc += 1; steps += 1
        if op == 'BNZ':
            if previous is None:
                raise ValueError('Branch must follow arithmetic')
            if previous != 0:
                pc = labels[arg]
            previous = None
        else:
            index = int(arg[1])
            if op == 'DEC' and registers[index] == 0:
                raise ValueError('Decrement of zero is forbidden')
            registers[index] += 1 if op == 'INC' else -1
            previous = registers[index]
    return registers, steps
