"""Priority encoder hierarchy with independently arbitrary inactive local codes.

Combinational model. Highest input number has highest priority. The four local
encoders, group encoder and mux are separate functions/wires, not an OR of codes.
"""


def pe4(word: int, invalid_code: int = 0) -> tuple[int, int]:
    if not 0 <= word < 16 or not 0 <= invalid_code < 4:
        raise ValueError("four-bit input and two-bit invalid code required")
    for index in (3, 2, 1, 0):
        if (word >> index) & 1:
            return 1, index
    return 0, invalid_code


def hierarchy(word: int, invalid_codes=(0, 0, 0, 0), *, fifth: bool = True,
              upper_invalid: int = 0) -> tuple[int, int]:
    if type(word) is not int or not 0 <= word < 65536:
        raise ValueError("sixteen-bit input required")
    if len(invalid_codes) != 4 or any(not 0 <= code < 4 for code in invalid_codes):
        raise ValueError("four two-bit invalid local codes required")
    local = [pe4((word >> (4 * g)) & 15, invalid_codes[g]) for g in range(4)]
    v = [pair[0] for pair in local]
    if fifth:
        valid, group = pe4(sum(bit << g for g, bit in enumerate(v)), upper_invalid)
    else:
        valid = v[3] | v[2] | v[1] | v[0]
        g1 = v[3] | v[2]
        g0 = v[3] | (v[1] & (1 ^ v[2]))
        group = (g1 << 1) | g0
    low = local[group][1]
    return valid, ((group << 2) | low) if valid else 0
