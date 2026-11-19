"""Count inclusive same-day timestamps with at most two decimal digits."""
def clock_seconds(value):
    if not isinstance(value, str) or len(value) != 8 or value[2] != ":" or value[5] != ":":
        raise ValueError("HH:MM:SS required")
    digits = value[:2] + value[3:5] + value[6:]
    if not all("0" <= c <= "9" for c in digits):
        raise ValueError("ASCII decimal digits required")
    h, m, s = int(value[:2]), int(value[3:5]), int(value[6:])
    if h >= 24 or m >= 60 or s >= 60:
        raise ValueError("Invalid time")
    return h * 3600 + m * 60 + s


def count_interesting_times(start, end):
    first, last = clock_seconds(start), clock_seconds(end)
    if first > last:
        raise ValueError("Same-day ordered interval required")
    count = 0
    for second in range(first, last + 1):
        h, remainder = divmod(second, 3600)
        m, s = divmod(remainder, 60)
        text = f"{h:02d}{m:02d}{s:02d}"
        if len(set(text)) <= 2:
            count += 1
    return count
