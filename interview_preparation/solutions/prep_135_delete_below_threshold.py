"""Stable removal via an external Del(index) that shrinks and shifts left.

The callback acts on the same list. Its own cost is NOT assumed free.
The second construction additionally permits writes and cheap tail deletion.
"""


def delete_below_backward(values, delete, threshold=19):
    for index in range(len(values) - 1, -1, -1):
        if values[index] < threshold:
            delete(index)
    return values


def compact_then_delete_tail(values, delete, threshold=19):
    write = 0
    for read in range(len(values)):
        if values[read] >= threshold:
            values[write] = values[read]
            write += 1
    while len(values) > write:
        delete(len(values) - 1)
    return values
