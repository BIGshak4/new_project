"""A legal 28-minute witness for the five-child canoe variant.

The separate checker proves optimality with exhaustive shortest-path models.
"""

TIMES = (1, 3, 6, 9, 11)
SCHEDULE = ((0, 1), (0,), (3, 4), (1,), (0, 2), (0,), (0, 1))


def replay_schedule(times=TIMES, schedule=SCHEDULE):
    if not times or any(not isinstance(t, int) or t <= 0 for t in times):
        raise ValueError("Crossing times must be positive integers")
    destination = set()
    boat, elapsed = 0, 0
    timeline = []
    for travellers in schedule:
        if len(travellers) not in (1, 2) or len(set(travellers)) != len(travellers):
            raise ValueError("One or two different children must accompany the canoe")
        for child in travellers:
            if child not in range(len(times)) or (child in destination) != bool(boat):
                raise ValueError("A traveller is not on the canoe's bank")
        duration = max(times[child] for child in travellers)
        for child in travellers:
            if boat:
                destination.remove(child)
            else:
                destination.add(child)
        elapsed += duration
        timeline.append((boat, tuple(travellers), duration, elapsed))
        boat ^= 1
    if len(destination) != len(times):
        raise ValueError("The schedule leaves a child on the initial bank")
    return elapsed, timeline
