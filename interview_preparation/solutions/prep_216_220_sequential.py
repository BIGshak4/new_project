"""Finite cycle models for PREP-216..220 and PREP-036 left-insertion variant.

Values are abstract unsigned words. These models are not HDL simulation.
"""

MOORE_101101 = ((0, 1), (2, 1), (0, 3), (2, 4), (5, 1), (0, 6), (2, 4))
LEFT_MOD3 = ((0, 2), (2, 1), (1, 0))


def divider_step(q0, q1, reset=False):
    return (0, 0) if reset else (1 - q0, q1 ^ q0)


def moore_step(state, bit, valid=True, reset=False):
    state = 0 if reset else MOORE_101101[state][bit] if valid else state
    return state, bool(state == 6)


def mealy_step(state, bit, valid=True, reset=False):
    if reset:
        return 0, False
    if not valid:
        return state, False
    hit = state == 5 and bit == 1
    return (3 if hit else MOORE_101101[state][bit]), hit


class ShiftDetector:
    def __init__(self):
        self.window = 0

    def step(self, bit, valid=True, reset=False):
        if reset:
            self.window = 0
            return False
        if not valid:
            return self.window == 0b101101
        self.window = ((self.window << 1) | bit) & 63
        return self.window == 0b101101


class WordMatcher:
    """Invalid cycles skip; configuration flushes the accepted-value streak."""
    def __init__(self, stored=(), pair=False, width=64):
        if len(stored) > 2:
            raise ValueError('At most two enrolled values')
        self.width = width
        self.mask = (1 << width) - 1
        if any(type(x) is not int or not 0 <= x <= self.mask for x in stored):
            raise ValueError('Word outside declared width')
        self.stored = tuple(stored)
        self.pair = pair
        self.previous_hit = False

    def step(self, value, valid=True, reset=False):
        if reset:
            self.stored = ()
            self.previous_hit = False
            return False
        if not valid:
            return False
        if type(value) is not int or not 0 <= value <= self.mask:
            raise ValueError('Word outside declared width')
        hit = value in self.stored
        output = hit and (self.previous_hit or not self.pair)
        self.previous_hit = hit
        return bool(output)


class InfixEvaluator:
    """Accepted NUMBER / PLUS / TIMES / EQUAL tokens; modulo 2**width.

    expect_number and pending_mul are the finite controller. Invalid grammar
    raises ValueError (the RTL instead emits error and resets the expression).
    Idle cycles do not consume tokens. EQUAL returns a one-cycle result.
    """
    def __init__(self, width=16):
        if width < 1:
            raise ValueError('Positive width required')
        self.mask = (1 << width) - 1
        self.reset()

    def reset(self):
        self.sum = self.product = 0
        self.expect_number = True
        self.pending_mul = False

    def step(self, token, valid=True, reset=False):
        if reset:
            self.reset()
            return None
        if not valid:
            return None
        if self.expect_number:
            if type(token) is not int or not 0 <= token <= self.mask:
                self.reset()
                raise ValueError('Expected unsigned W-bit operand')
            self.product = ((self.product * token) if self.pending_mul else token) & self.mask
            self.expect_number = False
        elif token == '*':
            self.pending_mul = True
            self.expect_number = True
        elif token == '+':
            self.sum = (self.sum + self.product) & self.mask
            self.pending_mul = False
            self.expect_number = True
        elif token == '=':
            result = (self.sum + self.product) & self.mask
            self.reset()
            return result
        else:
            self.reset()
            raise ValueError('Expected operator or final equals')
        return None


class FourWordMemory:
    """1R1W, synchronous read, read-first collision, zero-initialized reset."""
    def __init__(self, width=8):
        self.mask = (1 << width) - 1
        self.words = [0] * 4
        self.read_data = 0
        self.valid = False

    def step(self, wr_addr=0, wr_data=0, wr_en=False, re_addr=0, re_en=False, reset=False):
        if reset:
            self.words = [0] * 4
            self.read_data = 0
            self.valid = False
        else:
            self.valid = bool(re_en)
            if re_en:
                self.read_data = self.words[re_addr]
            if wr_en:
                self.words[wr_addr] = wr_data & self.mask
        return self.read_data, self.valid


class LeftModulo3:
    """Invariant state == N * inverse(2**k) mod 3, newest bit at left."""
    def __init__(self):
        self.state = 0
        self.seen = False

    def step(self, bit, valid=True, reset=False):
        if reset:
            self.state, self.seen = 0, False
        elif valid:
            self.state = LEFT_MOD3[self.state][bit]
            self.seen = True
        return bool(self.seen and self.state == 0)
