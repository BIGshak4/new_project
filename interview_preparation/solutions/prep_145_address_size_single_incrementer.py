"""Address+SIZE, using one functional eight-bit incrementer and routing/gates."""


def increment8(value):
    """One eight-bit +1 block; its output wraps, no carry port assumed."""
    return (value + 1) & 255


def address_plus_size(address, size, *, incrementer=increment8):
    """Return (valid, exact nine-bit result); invalid SIZE has result zero."""
    if type(address) is not int or not 0 <= address < 256:
        raise ValueError("Address must be eight unsigned bits")
    if type(size) is not int or not 0 <= size < 8:
        raise ValueError("SIZE must be three bits")
    valid = size in (1, 2, 4)
    k = {1: 0, 2: 1, 4: 2}.get(size, 0)
    # A pre-MUX selects zero-filled fixed wiring; not a variable arithmetic unit.
    upper = address >> k
    inc = incrementer(upper)  # Exactly one use of the sole functional block.
    if not 0 <= inc <= 255:
        raise ValueError("Incrementer output must be eight bits")
    # Post-MUX selects fixed shifts. Low k bits bypass the incrementer.
    low_mask = (1 << k) - 1
    routed = (inc << k) | (address & low_mask)
    # Only k=0 can overflow the eight-bit incrementer itself.
    carry = int(size == 1 and all((address >> bit) & 1 for bit in range(8)))
    result = routed | (carry << 8)
    return valid, result if valid else 0
