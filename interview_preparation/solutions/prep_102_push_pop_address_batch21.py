"""Address-indexed allocation, not a LIFO stack or FIFO queue."""


class AddressMemory:
    def __init__(self, depth=32, width=32):
        if depth < 1 or width < 1:
            raise ValueError("positive depth and payload width required")
        self.depth, self.width = depth, width
        self.occupied = set()
        self.payload = [None] * depth

    def tick(self, *, push=False, data=0, pop_address=None, reset=False):
        if not 0 <= data < 1 << self.width:
            raise ValueError("payload exceeds the declared width")
        if reset:
            self.occupied.clear()  # payload RAM is intentionally not scrubbed
            return {"push_success": False, "push_address": None, "pop_success": False}
        pop_success = pop_address in self.occupied
        if pop_success:
            self.occupied.remove(pop_address)
        free = next((a for a in range(self.depth) if a not in self.occupied), None)
        success = bool(push and free is not None)
        if success:
            self.payload[free] = data
            self.occupied.add(free)
        return {"push_success": success, "push_address": free if success else None,
                "pop_success": pop_success}
