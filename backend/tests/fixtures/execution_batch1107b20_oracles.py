"""Independent admin oracles, distinct from candidate implementations."""


def move_oracle(data, x, y):
    bits = [(byte >> bit) & 1 for byte in data for bit in range(8)]
    indices = [(x + j) % 1024 for j in range(y + 1)]
    arc = [bits[index] for index in indices]
    rotated = arc[1:] + arc[:1]
    for index, bit in zip(indices, rotated, strict=True):
        bits[index] = bit
    return [sum(bits[8 * i + bit] << bit for bit in range(8)) for i in range(128)]


def reverse_oracle(n):
    answer = int(str(abs(n))[::-1]) * (-1 if n < 0 else 1)
    return answer if -(1 << 31) <= answer < (1 << 31) else 0


def relative_oracle(a1, a2):
    rank = {value: index for index, value in enumerate(a2)}
    return sorted(a1, key=lambda v: (0, rank[v]) if v in rank else (1, v))


ORACLES = {
    'prep-circular-packed-bit-array-move': move_oracle,
    'prep-reverse-signed-decimal-integer': reverse_oracle,
    'prep-relative-sort-by-second-array': relative_oracle,
}
