"""Both workers call wait once at the same checkpoint in every loop."""
import threading


class TwoThreadBarrier:
    def __init__(self):
        self.condition = threading.Condition()
        self.arrived = 0
        self.generation = 0

    def wait(self):
        with self.condition:
            generation = self.generation
            self.arrived += 1
            if self.arrived == 2:
                self.arrived = 0
                self.generation += 1
                self.condition.notify_all()
            else:
                while generation == self.generation:
                    self.condition.wait()
