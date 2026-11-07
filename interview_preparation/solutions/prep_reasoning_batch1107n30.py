"""Finite, deterministic reference models; no network or physical hardware access."""
from random import Random


def packetize(total, cap, rng):
    """Partition a per-port total >=2 into packets in [2, cap]."""
    if type(total) is not int or total < 2 or type(cap) is not int or cap < 3:
        raise ValueError("total>=2 and cap>=3 required")
    remaining = total
    while remaining:
        upper = min(remaining, cap)
        skip = remaining - 1
        skip_present = 2 <= skip <= upper
        choices = upper - 1 - int(skip_present)
        size = 2 + rng.randrange(choices)
        if skip_present and size >= skip:
            size += 1
        yield size
        remaining -= size


def router_plan(total, active_count, seed=1, cap=65536):
    """Each chosen port is exercised. Sizes vary; partitions are not globally uniform."""
    if type(active_count) is not int or not 1 <= active_count <= 16:
        raise ValueError("active_count must be in1..16")
    if type(total) is not int or total < 2 * active_count:
        raise ValueError("total must be at least2*active_count")
    rng = Random(seed)
    ports = rng.sample(range(16), active_count)
    extra = total - 2 * active_count
    budgets = []
    for index in range(active_count):
        take = extra if index == active_count - 1 else rng.randrange(extra + 1)
        budgets.append(2 + take)
        extra -= take
    result = []
    for port, budget in zip(ports, budgets):
        result.extend((port, size) for size in packetize(budget, cap, rng))
    rng.shuffle(result)
    return ports, result


def random_router_test(max_total, seed, send_data):
    """send_data(port,size) synchronously accepts all bytes or raises an exception."""
    if type(max_total) is not int or not 2 <= max_total <= 1_000_000:
        raise ValueError("max_total must be in2..1000000")
    rng = Random(seed)
    active_count = rng.randint(1, min(16, max_total // 2))
    total = rng.randint(2 * active_count, max_total)
    ports, packets = router_plan(total, active_count, rng.getrandbits(64))
    for port, size in packets:
        send_data(port, size)
    return {"total": total, "ports": ports, "packet_count": len(packets)}


def counter_0121(phase):
    if type(phase) is not int or not 0 <= phase < 4:
        raise ValueError("phase must be0..3")
    return ((phase >> 1) & (1 ^ (phase & 1))) * 2 + (phase & 1), (phase + 1) % 4


def room_step(occupancy, event):
    """event:0idle,1entry,2exit,3invalid; rejected events hold occupancy."""
    if type(occupancy) is not int or not 0 <= occupancy <= 3:
        raise ValueError("occupancy must be0..3")
    if type(event) is not int or not 0 <= event <= 3:
        raise ValueError("event must be0..3")
    rejected = event == 3 or (event == 1 and occupancy == 3) or (event == 2 and occupancy == 0)
    if not rejected:
        occupancy += int(event == 1) - int(event == 2)
    return occupancy, bool(occupancy), rejected


def delayed_left_div3(bits):
    """After edge k report nonempty prefix k-1. New accepted bit becomes the MSB."""
    state, seen = 0, False
    output = []
    for bit in bits:
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError("bits must be integers0or1")
        output.append(bool(seen and state == 0))
        state = (2 * (state + bit)) % 3
        seen = True
    return output


def gold_payments():
    """Pieces are physical identities; each ownership mask is a daily balance."""
    pieces = (1, 2, 4)
    previous_mask = 0
    result = []
    for day in range(1, 8):
        mask = day
        give = [pieces[i] for i in range(3) if mask & (1 << i) and not previous_mask & (1 << i)]
        take_back = [pieces[i] for i in range(3) if previous_mask & (1 << i) and not mask & (1 << i)]
        result.append({"day": day, "give": give, "take_back": take_back,
                       "holds": [pieces[i] for i in range(3) if mask & (1 << i)]})
        previous_mask = mask
    return result
