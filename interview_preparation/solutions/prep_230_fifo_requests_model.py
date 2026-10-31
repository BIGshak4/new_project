"""Single-owner ring FIFO; each call snapshots requests and writes before read.

Empty+both passes the newly written value through. Full+both rejects the write,
then reads the oldest value. Rejected operations leave their own effect absent.
This model is not an ISR lock-free implementation.
"""


class RequestFifo:
    def __init__(self, capacity):
        if type(capacity) is not int or capacity <= 0:
            raise ValueError('positive capacity required')
        self.data = [0] * capacity
        self.capacity = capacity
        self.read_head = self.write_head = 0
        self.is_full, self.is_empty = False, True

    def step(self, write_request, write_value, read_request):
        wrote = bool(write_request and not self.is_full)
        if wrote:
            self.data[self.write_head] = write_value
            self.write_head = (self.write_head + 1) % self.capacity
            self.is_empty = False
            self.is_full = self.write_head == self.read_head
        read = bool(read_request and not self.is_empty)
        value = None
        if read:
            value = self.data[self.read_head]
            self.read_head = (self.read_head + 1) % self.capacity
            self.is_full = False
            self.is_empty = self.read_head == self.write_head
        return {'wrote': wrote, 'read': read, 'value': value}

    def contents(self):
        size = self.capacity if self.is_full else (self.write_head - self.read_head) % self.capacity
        return [self.data[(self.read_head + i) % self.capacity] for i in range(size)]


def fifo_trace(capacity, operations):
    queue = RequestFifo(capacity)
    events = [queue.step(bool(w), value, bool(r)) for w, value, r in operations]
    return {'events': events, 'remaining': queue.contents(), 'read_head': queue.read_head,
            'write_head': queue.write_head, 'is_full': queue.is_full, 'is_empty': queue.is_empty}
