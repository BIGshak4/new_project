"""Systematic shortened Hamming(12,8) SEC and optional extended SECDED.

Conceptual encoding/decoding only; this is not synthesized memory hardware.
Bit position1 is the least significant codeword bit. Even parity is used.
"""

DATA_POSITIONS = (3, 5, 6, 7, 9, 10, 11, 12)
PARITY_POSITIONS = (1, 2, 4, 8)


def validate_word(value, bits):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError("Word outside the declared unsigned width")


def encode8(data):
    validate_word(data, 8)
    code = sum(((data >> i) & 1) << (position - 1) for i, position in enumerate(DATA_POSITIONS))
    for parity in PARITY_POSITIONS:
        bit = 0
        for position in range(1, 13):
            if position & parity:
                bit ^= (code >> (position - 1)) & 1
        code |= bit << (parity - 1)
    return code


def syndrome12(code):
    validate_word(code, 12)
    result = 0
    for position in range(1, 13):
        if (code >> (position - 1)) & 1:
            result ^= position
    return result


def extract8(code):
    return sum(((code >> (position - 1)) & 1) << i for i, position in enumerate(DATA_POSITIONS))


def decode12(code):
    """Valid only under the promise of at most one error among all twelve bits.

    A double error can masquerade as a correctable single error. A syndrome
    outside1..12 is rejected, but this does not detect every multiple fault.
    """
    syndrome = syndrome12(code)
    if syndrome > 12:
        raise ValueError("Outside the single-error model")
    corrected = code ^ (1 << (syndrome - 1)) if syndrome else code
    return extract8(corrected), syndrome


def encode13(data):
    code = encode8(data)
    return code | ((code.bit_count() & 1) << 12)


def decode13(code):
    """SECDED guarantees: correct one error, flag every pair, not arbitrary faults."""
    validate_word(code, 13)
    low = code & 0xFFF
    syndrome, odd = syndrome12(low), code.bit_count() & 1
    if not odd and syndrome:
        return None, "double_error"
    if odd and syndrome > 12:
        return None, "outside_model"
    if odd and syndrome:
        low ^= 1 << (syndrome - 1)
    return extract8(low), "corrected" if odd else "clean"
