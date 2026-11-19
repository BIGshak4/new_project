"""A combinational model. All data pins and select pins carry one bit."""

def mux(s, d0, d1):
    return (d0, d1)[s]

def xor(a, b):
    return mux(a, b, mux(b, 1, 0))

def mux4(s, data):
    a = mux(s & 1, data[0], data[1])
    b = mux(s & 1, data[2], data[3])
    return mux(s >> 1, a, b)

def mux8(s, data):
    return mux(s >> 2, mux4(s & 3, data[:4]), mux4(s & 3, data[4:]))

def logical_right(word, distance):
    bits = [(word >> i) & 1 for i in range(8)]
    for select_bit, stride in enumerate((1, 2, 4)):
        extended = bits + [0] * stride
        bits = [mux((distance >> select_bit) & 1, bits[i], extended[i + stride])
                for i in range(8)]
    return sum(bit << i for i, bit in enumerate(bits))

