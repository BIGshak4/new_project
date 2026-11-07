"""Zoom-only black-box queries: values are never read from a hidden array.

Callbacks: set_zoom(i) selects a valid setting; get_focus() measures it.
The instrument must be deterministic, settled and noiseless during the search.
Return (index, measured_focus); leave the instrument at the returned index.
"""
from math import isfinite


def _count(n):
    if type(n) is not int or n <= 0:
        raise ValueError("a positive number of settings is required")


def _measure(index, set_zoom, get_focus):
    set_zoom(index)
    value = get_focus()
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or isinstance(value, float) and not isfinite(value)):
        raise ValueError("focus must be a finite real number")
    return value


def scan_global_maximum(n, set_zoom, get_focus):
    """Guaranteed for arbitrary finite values; choose the lowest index on ties."""
    _count(n)
    best_index = 0
    best = _measure(0, set_zoom, get_focus)
    for index in range(1, n):
        candidate = _measure(index, set_zoom, get_focus)
        if candidate > best:
            best_index, best = index, candidate
    set_zoom(best_index)
    return best_index, best


def unimodal_maximum(n, set_zoom, get_focus):
    """Requires strict increase, optional maximum plateau, then strict decrease.

    A lower/nonmaximal plateau violates this contract. The algorithm does not
    certify unimodality: doing so in general requires examining all settings.
    """
    _count(n)
    left, right = 0, n - 1
    while left < right:
        middle = (left + right) // 2
        here = _measure(middle, set_zoom, get_focus)
        following = _measure(middle + 1, set_zoom, get_focus)
        if here < following:
            left = middle + 1
        else:
            right = middle
    return left, _measure(left, set_zoom, get_focus)
