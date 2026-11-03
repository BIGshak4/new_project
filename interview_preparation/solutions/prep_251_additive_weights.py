"""One copy of each positive integral weight; only addition is permitted."""


def binary_weights(maximum):
    if type(maximum) is not int or maximum < 0:
        raise ValueError('Nonnegative integer maximum required')
    weights = []
    value = 1
    while value <= maximum:
        weights.append(value)
        value *= 2
    return weights


def select_weights(target, weights):
    if type(target) is not int or target < 0:
        raise ValueError('Nonnegative integer target required')
    chosen = []
    remaining = target
    for weight in reversed(weights):
        if weight <= remaining:
            chosen.append(weight)
            remaining -= weight
    if remaining:
        raise ValueError('Target not represented by these binary weights')
    return chosen
