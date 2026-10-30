"""Lowest-index hierarchy and an eight-input AND/OR/NOT encoder model."""


def pe4_low(word, invalid_code=0):
    if type(word) is not int or not 0 <= word < 16 or not 0 <= invalid_code < 4:
        raise ValueError("four-bit input and two-bit invalid code required")
    for index in range(4):
        if word & (1 << index):
            return 1, index
    return 0, invalid_code


def pe16_low(word, invalid_codes=(0, 0, 0, 0), upper_invalid=0):
    if type(word) is not int or not 0 <= word < (1 << 16):
        raise ValueError("sixteen input bits required")
    if len(invalid_codes) != 4:
        raise ValueError("four inactive local codes required")
    local = [pe4_low((word >> (4 * group)) & 15, invalid_codes[group])
             for group in range(4)]
    valid, group = pe4_low(sum(v << i for i, (v, _) in enumerate(local)), upper_invalid)
    code = (group << 2) | local[group][1]
    return valid, code if valid else 0


def pe8_gates_low(word):
    if type(word) is not int or not 0 <= word < 256:
        raise ValueError("eight input bits required")
    grants, prefix = [], 0
    for index in range(8):
        bit = (word >> index) & 1
        grants.append(bit & (1 ^ prefix))
        prefix |= bit
    y0 = grants[1] | grants[3] | grants[5] | grants[7]
    y1 = grants[2] | grants[3] | grants[6] | grants[7]
    y2 = grants[4] | grants[5] | grants[6] | grants[7]
    return prefix, (y2 << 2) | (y1 << 1) | y0
