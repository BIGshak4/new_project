"""At most one helper swap guarantees every target within ceil(n/2) opens.

Box labels and note labels are 1..n; permutation[i-1] is the note in box i.
The helper does not need to know the later target. No message is sent afterward.
"""


def validate_permutation(permutation):
    n = len(permutation)
    seen = [False] * (n + 1)
    for note in permutation:
        if not isinstance(note, int) or not 1 <= note <= n or seen[note]:
            raise ValueError("Notes must be a permutation of labels 1..n")
        seen[note] = True


def prepare_boxes(permutation, limit=50):
    """Return a prepared copy and the swapped box labels, or None."""
    validate_permutation(permutation)
    n = len(permutation)
    if not isinstance(limit, int) or limit < 1 or n > 2 * limit:
        raise ValueError("This guarantee requires positive limit and n <= 2*limit")
    result = list(permutation)
    seen = [False] * (n + 1)
    for start in range(1, n + 1):
        if seen[start]:
            continue
        cycle = []
        current = start
        while not seen[current]:
            seen[current] = True
            cycle.append(current)
            current = result[current - 1]
        if len(cycle) > limit:
            # There can be at most one such cycle when n <= 2*limit.
            first, second = cycle[0], cycle[len(cycle) // 2]
            result[first - 1], result[second - 1] = result[second - 1], result[first - 1]
            return result, (first, second)
    return result, None


def find_target(read_note, target, limit=50, number_of_boxes=100):
    """Use only the query interface; return the number of boxes actually opened."""
    if target not in range(1, number_of_boxes + 1) or limit < 1:
        raise ValueError("Invalid target or query limit")
    box = target
    for count in range(1, limit + 1):
        note = read_note(box)
        if note == target:
            return count
        if note not in range(1, number_of_boxes + 1):
            raise ValueError("Query returned an invalid note label")
        box = note
    raise LookupError("Target was not found within the query limit")
