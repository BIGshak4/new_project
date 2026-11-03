"""Illustrative fixed-slot capacity model, not a load test of a real service.

Each slot may complete capacity requests. Admit at most capacity+queue_limit
requests including carried backlog. FIFO work left after service is bounded.
Uniform request costs, exact deterministic service, no retries or failures.
"""
from collections import deque
from fractions import Fraction


def required_instances(peak_per_second, measured_instance_capacity,
                       utilization=Fraction(3, 4), unavailable=1):
    if (type(peak_per_second) is not int or peak_per_second < 0 or
            type(measured_instance_capacity) is not int or measured_instance_capacity <= 0 or
            not 0 < utilization <= 1 or type(unavailable) is not int or unavailable < 0):
        raise ValueError('Invalid capacity inputs')
    utilization = Fraction(utilization)
    raw = Fraction(peak_per_second) / (measured_instance_capacity * utilization)
    working = (raw.numerator + raw.denominator - 1) // raw.denominator
    return working + unavailable


def simulate_slots(arrivals, capacity, queue_limit):
    if (type(capacity) is not int or capacity <= 0 or
            type(queue_limit) is not int or queue_limit < 0):
        raise ValueError('Positive slot capacity and nonnegative queue limit required')
    pending = deque()
    depth = 0
    trace = []
    for count in arrivals:
        if type(count) is not int or count < 0:
            raise ValueError('Nonnegative integer arrivals required')
        admitted = min(count, capacity + queue_limit - depth)
        rejected = count - admitted
        if admitted:
            pending.append(admitted)
        depth += admitted
        budget = capacity
        completed = 0
        while pending and budget:
            work = min(pending[0], budget)
            pending[0] -= work
            budget -= work
            depth -= work
            completed += work
            if pending[0] == 0:
                pending.popleft()
        trace.append(dict(arrived=count, admitted=admitted, rejected=rejected,
                          completed=completed, backlog=depth))
    return trace
