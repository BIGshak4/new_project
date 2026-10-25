"""Exact continuous transport phases and executable cache-trip witnesses.

The continuous model permits divisible cargo and arbitrary cache positions.
The integer witness uses whole bananas and stations at whole kilometres.
These are mathematical models, not measurements or a logistics application.
"""

from fractions import Fraction


def continuous_optimum(stock=3000, capacity=1000, distance=1000):
    stock, capacity, distance = map(Fraction, (stock, capacity, distance))
    if stock < 0 or capacity <= 0 or distance < 0:
        raise ValueError("nonnegative stock/distance and positive capacity required")
    position, stages = Fraction(0), []
    while position < distance and stock > 0:
        loads = -(-stock // capacity)
        traversals = 2 * loads - 1
        threshold = (loads - 1) * capacity
        stage_distance = min(distance - position, (stock - threshold) / traversals)
        after = stock - traversals * stage_distance
        stages.append({"start": position, "end": position + stage_distance,
                       "stock_before": stock, "stock_after": after,
                       "forward_trips": loads, "return_trips": loads - 1,
                       "consumption_per_km": traversals})
        position += stage_distance
        stock = after
    return stock if position == distance else Fraction(0), stages


class TripModel:
    """A supplied cache inventory plus one camel; load includes travel fuel."""

    def __init__(self):
        self.capacity = Fraction(1000)
        self.position = self.cargo = self.eaten = self.discarded = Fraction(0)
        self.caches = {Fraction(0): Fraction(3000)}
        self.log = []

    def _record(self, action, amount):
        assert 0 <= self.cargo <= self.capacity
        assert all(value >= 0 for value in self.caches.values())
        assert self.cargo + sum(self.caches.values()) + self.eaten + self.discarded == 3000
        self.log.append((action, self.position, Fraction(amount), self.cargo))

    def load(self, amount):
        amount = Fraction(amount)
        if amount < 0 or self.caches.get(self.position, 0) < amount or self.cargo + amount > self.capacity:
            raise ValueError("invalid load")
        self.caches[self.position] -= amount
        self.cargo += amount
        self._record("load", amount)

    def unload(self, amount):
        amount = Fraction(amount)
        if amount < 0 or amount > self.cargo:
            raise ValueError("invalid unload")
        self.cargo -= amount
        self.caches[self.position] = self.caches.get(self.position, 0) + amount
        self._record("unload", amount)

    def move(self, destination):
        destination = Fraction(destination)
        consumed = abs(destination - self.position)
        if not 0 <= destination <= 1000 or consumed > self.cargo:
            raise ValueError("insufficient carried fuel or destination outside road")
        self.cargo -= consumed
        self.eaten += consumed
        self.position = destination
        self._record("move", consumed)

    def discard(self, amount):
        amount = Fraction(amount)
        if amount < 0 or self.caches.get(self.position, 0) < amount:
            raise ValueError("invalid discard")
        self.caches[self.position] -= amount
        self.discarded += amount
        self._record("discard", amount)

    def transfer(self, destination, loads):
        """Canonical phase starts with exactly loads*1000 at this depot."""
        origin = self.position
        length = Fraction(destination) - origin
        if length <= 0 or self.caches.get(origin, 0) != loads * self.capacity:
            raise ValueError("phase requires a forward depot and complete initial loads")
        for _ in range(loads - 1):
            self.load(self.capacity)
            self.move(destination)
            self.unload(self.cargo - length)  # Keep the return fuel in the load.
            self.move(origin)
        self.load(self.capacity)
        self.move(destination)
        self.unload(self.cargo)


def canonical_plan(*, integer=False):
    journey = TripModel()
    journey.transfer(200, 3)
    journey.transfer(533 if integer else Fraction(1600, 3), 2)
    if integer:
        journey.discard(1)  # 1001 at km533; take 1000 for the final 467 km.
    journey.load(1000)
    journey.move(1000)
    journey.unload(journey.cargo)
    return journey
