"""Non-mutating Floyd detection and optional cycle-entry identification.

Node identity is tested, never equality of stored values. A finite static
singly linked structure with valid next references or None is promised.
"""


class Node:
    __slots__ = ("value", "next")

    def __init__(self, value, following=None):
        self.value, self.next = value, following


def _meeting(head):
    slow = fast = head
    while fast is not None:
        first = fast.next
        if first is None:
            return None
        slow = slow.next
        fast = first.next
        if slow is fast:
            return slow
    return None


def has_cycle(head):
    return _meeting(head) is not None


def cycle_entry(head):
    """Optional extension: return the cycle-entry node, or None."""
    meeting = _meeting(head)
    if meeting is None:
        return None
    seeker = head
    while seeker is not meeting:
        seeker = seeker.next
        meeting = meeting.next
    return seeker
