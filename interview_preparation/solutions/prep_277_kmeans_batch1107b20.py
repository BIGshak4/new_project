"""Deterministic bounded Lloyd steps; no global optimality guarantee."""
from math import isfinite


def lloyd(points, initial_indices, max_iter=100):
    if type(points) is not list or not points or type(initial_indices) is not list:
        raise ValueError("nonempty point list and initial indices required")
    dimension = len(points[0])
    if dimension < 1 or any(len(point) != dimension for point in points):
        raise ValueError("all points must have the same positive dimension")
    if any(type(v) not in (int, float) or not isfinite(v) or abs(v) > 1e100
           for point in points for v in point):
        raise ValueError("finite coordinates with magnitude at most 1e100 required")
    if (not initial_indices or len(initial_indices) > len(points)
            or len(set(initial_indices)) != len(initial_indices)
            or any(type(i) is not int or not 0 <= i < len(points) for i in initial_indices)
            or type(max_iter) is not int or max_iter < 1):
        raise ValueError("distinct valid initial indices and positive iteration budget required")
    # The demonstration bounds practical allocation and sum magnitude explicitly.
    if len(points) > 10000 or dimension > 64 or len(initial_indices) > 64:
        raise ValueError("demonstration size limit exceeded")
    centers = [[float(v) for v in points[i]] for i in initial_indices]
    previous = None
    for iteration in range(1, max_iter + 1):
        labels = []
        for point in points:
            best, best_distance = 0, float("inf")
            for j, center in enumerate(centers):
                distance = sum((point[d] - center[d]) ** 2 for d in range(dimension))
                if distance < best_distance:  # Exact ties retain lower index.
                    best, best_distance = j, distance
            labels.append(best)
        sums = [[0.0] * dimension for _ in centers]
        counts = [0] * len(centers)
        for point, label in zip(points, labels):
            counts[label] += 1
            for d in range(dimension):
                sums[label][d] += point[d]
        updated = [([v / counts[j] for v in sums[j]] if counts[j] else center[:])
                   for j, center in enumerate(centers)]
        objective = sum(sum((point[d] - updated[label][d]) ** 2 for d in range(dimension))
                        for point, label in zip(points, labels))
        converged = labels == previous
        centers, previous = updated, labels
        if converged:
            break
    return {"labels": labels, "centers": centers, "sse": objective,
            "iterations": iteration, "converged": converged}
