"""Count decimal strings by their last digit; never construct a 2000-digit integer."""


def allowed_pairs() -> tuple[int, ...]:
    return tuple(value for value in range(10, 100) if value % 17 == 0 or value % 23 == 0)


def ending_counts(length: int, first_digit: int = 3) -> dict[int, int]:
    """Exact counts under the overlapping, left-to-right adjacent-pair interpretation."""
    if length < 1 or not 1 <= first_digit <= 9:
        raise ValueError("Require a positive length and a nonzero decimal first digit")
    counts = [0] * 10
    counts[first_digit] = 1
    pairs = allowed_pairs()
    for _ in range(length - 1):
        following = [0] * 10
        for pair in pairs:
            previous, current = divmod(pair, 10)
            following[current] += counts[previous]
        counts = following
    return {digit: count for digit, count in enumerate(counts) if count}


def valid_numbers(length: int) -> list[str]:
    """Enumerate valid strings starting at 3; this particular graph has at most two per length."""
    if length < 1:
        raise ValueError("Require a positive length")
    candidates = ["3"]
    for _ in range(length - 1):
        candidates = [prefix + str(pair % 10)
                      for prefix in candidates for pair in allowed_pairs()
                      if int(prefix[-1]) == pair // 10]
    return candidates


if __name__ == "__main__":
    counts = ending_counts(2000)
    print("Counts by last digit:", counts)
    print("Total valid numbers:", sum(counts.values()))
