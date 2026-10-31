"""Read-only fixed-pattern coverage, with explicit endian and boundary rules."""


def expected_word(address, endian):
    if not 0 <= address <= 252 or endian not in ('little', 'big'):
        raise ValueError('Four-byte reads must stay inside 256 bytes')
    shifts = range(0, 32, 8) if endian == 'little' else range(24, -1, -8)
    return sum((address + offset) << shift for offset, shift in enumerate(shifts))


def validate(read, endian, all_offsets=False):
    """Return (pass,read_count); read may return a signed 32-bit representation."""
    addresses = range(253) if all_offsets else range(0, 253, 4)
    count = 0
    for address in addresses:
        count += 1
        if (read(address) & 0xffffffff) != expected_word(address, endian):
            return False, count
    return True, count
