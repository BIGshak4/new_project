"""Exact small-instance assignment with a declared lexicographic objective.

Maximize (number receiving an acceptable costume, number receiving first
choice). Each named costume exists once. An unassigned person receives None.
Exponential search is intentional because the source imposes no time bound.
"""


def best_costume_assignment(costumes, preferences):
    inventory = tuple(costumes)
    if any(not isinstance(item, str) for item in inventory) or len(set(inventory)) != len(inventory):
        raise ValueError("inventory must contain distinct costume names")
    available = set(inventory)
    choices = tuple(tuple(person) for person in preferences)
    for person in choices:
        if (len(person) > 2 or any(not isinstance(item, str) for item in person)
                or len(set(person)) != len(person) or any(item not in available for item in person)):
            raise ValueError("each person needs at most two distinct inventory preferences")
    best_score, best = (-1, -1), None
    current, used = [], set()

    def visit(index, served, first):
        nonlocal best_score, best
        if index == len(choices):
            score = served, first
            if score > best_score:
                best_score, best = score, tuple(current)
            return
        for rank, item in enumerate(choices[index]):
            if item in used:
                continue
            used.add(item)
            current.append(item)
            visit(index + 1, served + 1, first + int(rank == 0))
            current.pop()
            used.remove(item)
        current.append(None)
        visit(index + 1, served, first)
        current.pop()

    visit(0, 0, 0)
    return {"assignment": best, "score": best_score}
