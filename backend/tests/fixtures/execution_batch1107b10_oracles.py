"""Test-only oracle independent of the in-place heapsort candidate."""


def sort_oracle(values):
    return sorted(values)


ORACLES = {'prep-general-in-place-integer-array-sort': sort_oracle}
