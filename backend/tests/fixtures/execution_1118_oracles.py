"""Independent expected outputs for the November 18 runtime contracts."""


def copied_array(values, source, size, target):
    return values[:target] + values[source:source + size] + values[target + size:]


def random_from_ranks(low, high, ranks):
    output = []
    for rank in ranks:
        allowed = [value for value in range(low, high + 1) if value not in output[-5:]]
        output.append(allowed[rank])
    return output


def successors(keys):
    ordered = sorted(keys)
    next_keys = dict(zip(ordered, ordered[1:] + [None]))
    return [next_keys[key] for key in keys]


ORACLES = {
    'prep-checked-c-string-copy-contract': copied_array,
    'prep-uniform-random-except-last-five': random_from_ranks,
    'prep-bst-inorder-successor-parent-pointers': successors,
}
