"""Four-input descending sorting network; one comparator may unconditionally swap."""
COMPARATORS = ((0, 1), (2, 3), (0, 2), (1, 3), (1, 2))
TEST_VECTOR = (4, 3, 2, 1)
SIGNATURES = {
    (4, 3, 2, 1): 'healthy',
    (3, 4, 2, 1): 'C1',
    (4, 3, 1, 2): 'C2',
    (2, 4, 3, 1): 'C3',
    (4, 2, 1, 3): 'C4',
    (4, 2, 3, 1): 'C5',
}


def run_network(values, faulty=None):
    if len(values) != 4 or faulty not in (None, 1, 2, 3, 4, 5):
        raise ValueError('Four values and zero or one faulty component required')
    wires = list(values)
    for component, (i, j) in enumerate(COMPARATORS, 1):
        a, b = wires[i], wires[j]
        # The source cell has MAX on its upper output, MIN below.
        wires[i], wires[j] = (b, a) if component == faulty else (max(a, b), min(a, b))
    return tuple(wires)


def diagnose(observed_output):
    """Valid only when TEST_VECTOR was applied and the specified fault model holds."""
    result = SIGNATURES.get(tuple(observed_output))
    if result is None:
        raise ValueError('Output inconsistent with specified input/topology/single-swap fault model')
    return result
