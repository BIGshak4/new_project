"""Executable integer model of the separately supplied C divide-and-conquer."""

def closest_pair(points):
    if len(points) < 2 or any(abs(c) > 10**9 or type(c) is not int for p in points for c in p):
        raise ValueError('At least two bounded integer points are required')
    a = sorted((x, y, i) for i, (x, y) in enumerate(points))
    best = [2**64 - 1, None, None]

    def consider(p, q):
        d = (p[0]-q[0])**2 + (p[1]-q[1])**2
        if d < best[0]:
            best[:] = [d, p[2], q[2]]

    def solve(items):
        if len(items) <= 3:
            for i, p in enumerate(items):
                for q in items[i+1:]:
                    consider(p, q)
            return sorted(items, key=lambda p: (p[1], p[0], p[2]))
        mid = len(items)//2
        split = items[mid][0]
        left, right = solve(items[:mid]), solve(items[mid:])
        merged = []; i = j = 0
        while i < len(left) and j < len(right):
            if (left[i][1], left[i][0], left[i][2]) <= (right[j][1], right[j][0], right[j][2]):
                merged.append(left[i]); i += 1
            else:
                merged.append(right[j]); j += 1
        merged.extend(left[i:]); merged.extend(right[j:])
        if best[0]:
            strip = [p for p in merged if (p[0]-split)**2 < best[0]]
            for i, p in enumerate(strip):
                for j in range(i+1, len(strip)):
                    if (strip[j][1]-p[1])**2 >= best[0]:
                        break
                    consider(p, strip[j])
        return merged
    solve(a)
    return tuple(best)
