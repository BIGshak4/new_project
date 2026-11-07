"""Ideal event-level model of the supplied two-clock registered-flag FIFO.

Calls represent separated clock edges. No metastability/analog delay is modeled.
Queue correctness must be checked by an independent accepted-operation oracle.
"""


class GrayFifo:
    def __init__(self, address_bits=2):
        if type(address_bits) is not int or address_bits < 1:
            raise ValueError('address_bits must be positive')
        self.aw = address_bits
        self.depth = 1 << address_bits
        self.mask = 2 * self.depth - 1
        self.memory = [None] * self.depth
        self.wbin = self.wgray = self.rbin = self.rgray = 0
        self.wq1 = self.wq2 = self.rq1 = self.rq2 = 0
        self.full, self.empty = False, True
        self.rdata, self.rvalid = None, False

    def write_edge(self, request=False, data=None):
        take = bool(request and not self.full)
        next_binary = (self.wbin + take) & self.mask
        next_gray = (next_binary >> 1) ^ next_binary
        next_full = next_gray == (self.wq2 ^ (self.depth | (self.depth >> 1)))
        if take:
            self.memory[self.wbin & (self.depth - 1)] = data
        self.wq2, self.wq1 = self.wq1, self.rgray
        self.wbin, self.wgray, self.full = next_binary, next_gray, next_full
        return take

    def read_edge(self, request=False):
        take = bool(request and not self.empty)
        next_binary = (self.rbin + take) & self.mask
        next_gray = (next_binary >> 1) ^ next_binary
        next_empty = next_gray == self.rq2
        if take:
            self.rdata = self.memory[self.rbin & (self.depth - 1)]
        self.rvalid = take
        self.rq2, self.rq1 = self.rq1, self.wgray
        self.rbin, self.rgray, self.empty = next_binary, next_gray, next_empty
        return take, self.rdata
