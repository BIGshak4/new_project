"""Active-high one-hot decoder, data masking and reduction OR."""


def decoder_mux(data, select):
    count = len(data)
    if count < 2 or count & (count - 1) or not 0 <= select < count:
        raise ValueError('power-of-two input count and valid select required')
    if any(v not in (0, 1) for v in data):
        raise ValueError('binary data required')
    decoded = [int(select == index) for index in range(count)]
    terms = [bit & enable for bit, enable in zip(data, decoded)]
    out = 0
    for term in terms:
        out |= term
    return out, decoded
