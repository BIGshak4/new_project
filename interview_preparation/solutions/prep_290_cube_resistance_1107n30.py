"""Exact nodal analysis: cube vertices 0..7; terminals 000 and 111."""
from fractions import Fraction


def cube_resistance(edge_ohms=1):
    resistance = Fraction(edge_ohms)
    if resistance <= 0:
        raise ValueError("Every edge resistance must be positive")
    interior = list(range(1, 7))
    rows = []
    for vertex in interior:
        row = [Fraction(0)] * 7
        row[interior.index(vertex)] = 3
        for mask in (1, 2, 4):
            neighbor = vertex ^ mask
            if neighbor == 0:
                row[-1] += 1  # terminal A is held at one volt
            elif neighbor != 7:
                row[interior.index(neighbor)] -= 1
        rows.append(row)
    for column in range(6):
        pivot = next(r for r in range(column, 6) if rows[r][column])
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [v / divisor for v in rows[column]]
        for r in range(6):
            if r != column:
                factor = rows[r][column]
                rows[r] = [a - factor*b for a,b in zip(rows[r], rows[column])]
    voltage = {0: Fraction(1), 7: Fraction(0)}
    voltage.update({v: rows[i][-1] for i,v in enumerate(interior)})
    current = sum((1-voltage[v])/resistance for v in (1,2,4))
    return 1/current, voltage
