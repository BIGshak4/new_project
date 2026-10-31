"""External accepted-arrival/completion monitor with observable packet IDs.

This is a declared interface completion: without IDs/FIFO or complete event
observation, exact completed-packet average may be impossible. Timestamp units
are arbitrary, monotone, exact; all events are serialized. Initially empty.
"""
from fractions import Fraction


class ResidenceMonitor:
    def __init__(self):
        self._pending = {}
        self._time = None
        self._area = 0
        self._total = 0
        self._count = 0

    def _advance(self, time):
        if type(time) is not int or time < 0 or (self._time is not None and time < self._time):
            raise ValueError('Require nonnegative monotone integer timestamps')
        if self._time is not None:
            self._area += len(self._pending) * (time - self._time)
        self._time = time

    def arrive(self, packet_id, time):
        if packet_id in self._pending:
            raise ValueError('Packet ID already pending')
        self._advance(time)
        self._pending[packet_id] = time

    def depart(self, packet_id, time):
        if packet_id not in self._pending:
            raise ValueError('Unknown departure')
        self._advance(time)
        self._total += time - self._pending.pop(packet_id)
        self._count += 1

    def query(self, time):
        """Return exact means for completed packets and currently resident ages."""
        self._advance(time)
        completed_average = Fraction(self._total, self._count) if self._count else None
        pending_age_total = self._area - self._total
        pending_average_age = Fraction(pending_age_total, len(self._pending)) if self._pending else None
        return {'completed_average': completed_average,
                'pending_average_age': pending_average_age,
                'occupancy_area': self._area,
                'completed_count': self._count,
                'pending_count': len(self._pending)}
