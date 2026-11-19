class Receiver:
    """Call feed exactly once for each newly delivered character."""

    def __init__(self, push, pop, is_empty):
        self.push = push
        self.pop = pop
        self.is_empty = is_empty
        self.reading_y = False
        self.valid = True

    def feed(self, character):
        if character == "\\":
            return self.valid and self.is_empty()
        if not self.valid:
            return None
        if character == "x" and not self.reading_y:
            self.push(1)
            self.push(1)
        elif character == "y" and not self.is_empty():
            self.reading_y = True
            self.pop()
        else:
            self.valid = False
        return None


def accepts_frame(transmission):
    stack = []
    receiver = Receiver(stack.append, stack.pop, lambda: not stack)
    for character in transmission:
        answer = receiver.feed(character)
        if answer is not None:
            return answer
    return False
