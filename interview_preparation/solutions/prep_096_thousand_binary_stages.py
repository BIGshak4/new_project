"""Local replies for grouped two-thirds and global all-but-one guarantees."""


def group_sizes(n):
    if type(n) is not int or n < 3:
        raise ValueError("group construction specified for n>=3")
    triples, remainder = divmod(n, 3)
    if remainder == 0:
        return (3,) * triples
    return (3,) * (triples - 1) + (3 + remainder,)


def grouped_reply(visible, heard, groups):
    step = len(heard)
    start = 0
    for size in groups:
        if step < start + size:
            local = step - start
            if local == 0:
                return sum(visible[-(size - 1) :]) % 2
            remaining = size - 1 - local
            still_visible = visible[-remaining:] if remaining else ()
            correct_heard = heard[start + 1 :]
            return (heard[start] + sum(still_visible) + sum(correct_heard)) % 2
        start += size
    raise ValueError("speaker index lies outside the agreed groups")


def global_reply(visible, heard):
    return (sum(visible) + sum(heard)) % 2


def simulate(hats, grouped=False):
    hats = tuple(hats)
    if not hats or any(type(x) is not int or x not in (0, 1) for x in hats):
        raise ValueError("nonempty binary hat line required")
    groups = group_sizes(len(hats)) if grouped else ()
    heard, correct = [], []
    for index in range(len(hats) - 1, -1, -1):
        visible = hats[:index]
        answer = (
            grouped_reply(visible, heard, groups)
            if grouped
            else global_reply(visible, heard)
        )
        heard.append(answer)
        correct.append(answer == hats[index])
    return tuple(heard), tuple(correct)
