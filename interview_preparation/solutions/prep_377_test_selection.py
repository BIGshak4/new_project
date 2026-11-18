"""Select equal-cost tests after the caller vets them against known-good controls."""


def choose_tests(failures, required, mandatory=()):
    """Return test names covering the named historical faults, or reject missing coverage."""
    selected = list(dict.fromkeys(mandatory))
    remaining = set(required)
    for name in selected:
        remaining.difference_update(failures[name])
    available = [name for name in failures if name not in selected]
    while remaining:
        if not available:
            raise ValueError("required fault lacks coverage")
        best = max(available, key=lambda name: len(remaining.intersection(failures[name])))
        if remaining.isdisjoint(failures[best]):
            raise ValueError("required fault lacks coverage")
        selected.append(best)
        remaining.difference_update(failures[best])
        available.remove(best)
    return selected

