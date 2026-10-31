"""Move integer zeroes to the end in place, preserving nonzero order."""


def move_zeroes(values):
    write = 0
    for read in range(len(values)):
        if values[read] != 0:
            values[write] = values[read]
            write += 1
    for index in range(write, len(values)):
        values[index] = 0
    return values
