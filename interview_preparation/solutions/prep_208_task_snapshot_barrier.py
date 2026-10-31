"""Barrier for accepted tasks, allowing arbitrary completion order.

Methods describe serialized atomic events. In a concurrent implementation all
operations must share a lock/event ordering; dispatch only after accept().
IDs never wrap or repeat. Cancelled/failed work needs an explicit terminal policy.
"""
from threading import Condition, Lock


class SnapshotBarrier:
    def __init__(self):
        self._condition = Condition(Lock())
        self._accepted = 0
        self._prefix = 0
        self._completed_above_prefix = set()

    def accept(self):
        """Assign an ID before the task can be dispatched to the engine."""
        with self._condition:
            self._accepted += 1
            return self._accepted

    def press(self):
        """Snapshot and acceptance are ordered by the same lock."""
        with self._condition:
            return self._accepted

    def complete(self, ident):
        with self._condition:
            if type(ident) is not int or not 1 <= ident <= self._accepted:
                raise ValueError('Unknown completion ID')
            if ident <= self._prefix or ident in self._completed_above_prefix:
                raise ValueError('Duplicate completion')
            self._completed_above_prefix.add(ident)
            while self._prefix + 1 in self._completed_above_prefix:
                self._prefix += 1
                self._completed_above_prefix.remove(self._prefix)
            self._condition.notify_all()

    def ready(self, target):
        with self._condition:
            if type(target) is not int or not 0 <= target <= self._accepted:
                raise ValueError('Invalid snapshot target')
            return self._prefix >= target

    def wait(self, target, timeout=None):
        """Wake on completions; recheck the predicate after every wakeup."""
        with self._condition:
            if type(target) is not int or not 0 <= target <= self._accepted:
                raise ValueError('Invalid snapshot target')
            return self._condition.wait_for(lambda: self._prefix >= target, timeout)
