"""Count exactly bit_length low-first packed bits; unused tail bits ignored."""


def count_packed_ones(data, bit_length):
    if type(bit_length) is not int or not 0 <= bit_length <= 8 * len(data):
        raise ValueError('valid bit length required')
    full, tail = divmod(bit_length, 8)
    total = 0
    for index in range(full + bool(tail)):
        value = data[index]
        if tail and index == full:
            value &= (1 << tail) - 1
        while value:
            value &= value - 1
            total += 1
    return total
