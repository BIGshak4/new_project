"""Unique visible permutations of Python Unicode code points, any order."""


def unique_permutations(text):
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    counts = {}
    for character in text:
        counts[character] = counts.get(character, 0) + 1
    alphabet = tuple(counts)
    path = []

    def visit():
        if len(path) == len(text):
            yield "".join(path)
            return
        for character in alphabet:
            if counts[character] == 0:
                continue
            counts[character] -= 1
            path.append(character)
            yield from visit()
            path.pop()
            counts[character] += 1

    return visit()


def print_permutations(text, write=print):
    for permutation in unique_permutations(text):
        write(permutation)
