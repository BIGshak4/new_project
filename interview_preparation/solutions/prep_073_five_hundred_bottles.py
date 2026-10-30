"""One parallel round at the24-hour endpoint; nine needed,ten available."""


def tasting_groups(testers=9):
    if type(testers) is not int or testers not in (9, 10):
        raise ValueError("use nine or ten available binary endpoint testers")
    return tuple(
        tuple(bottle for bottle in range(1, 501) if ((bottle - 1) >> bit) & 1)
        for bit in range(testers)
    )


def decode(dead):
    dead = tuple(dead)
    if len(dead) not in (9, 10) or any(type(x) is not bool for x in dead):
        raise ValueError("nine or ten Boolean endpoint outcomes required")
    label = sum(1 << bit for bit, value in enumerate(dead) if value)
    if label >= 500:
        raise ValueError("unused pattern violates the declared single-poison model")
    return label + 1
