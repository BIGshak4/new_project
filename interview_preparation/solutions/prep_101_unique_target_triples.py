"""Return each sorted VALUE triple once, using three distinct occurrences.

The source's ALL-triples wording is ambiguous. This is the explicitly added
unique-value contract. Enumerating every index triple may require cubic output.
"""


def unique_target_triples(values, target):
    ordered = sorted(values)
    output = []
    for first in range(len(ordered) - 2):
        if first and ordered[first] == ordered[first - 1]:
            continue
        left, right = first + 1, len(ordered) - 1
        while left < right:
            total = ordered[first] + ordered[left] + ordered[right]
            if total < target:
                left += 1
            elif total > target:
                right -= 1
            else:
                output.append((ordered[first], ordered[left], ordered[right]))
                low, high = ordered[left], ordered[right]
                while left < right and ordered[left] == low:
                    left += 1
                while left < right and ordered[right] == high:
                    right -= 1
    return output
