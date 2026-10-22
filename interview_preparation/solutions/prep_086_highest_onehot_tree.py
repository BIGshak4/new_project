"""One-hot MSB isolation by a serial prefix and a balanced two-pass tree."""
from dataclasses import dataclass


def validate(value: int, width: int) -> None:
    if width < 1 or value < 0 or value >= 1 << width:
        raise ValueError("positive width and fitting unsigned input required")


def cell2(high: int, low: int, higher_present: int = 0) -> tuple[int, int, int]:
    """Returns raw valid, high grant, low grant; raw valid ignores the mask."""
    if any(v not in (0, 1) for v in (high, low, higher_present)):
        raise ValueError("binary signals required")
    return high | low, high & (1 - higher_present), low & (1 - (higher_present | high))


def serial(value: int, width: int) -> int:
    validate(value, width)
    seen = grant = 0
    for bit in range(width - 1, -1, -1):
        request = (value >> bit) & 1
        grant |= (request & (1 - seen)) << bit
        seen |= request
    return grant


@dataclass(frozen=True)
class Node:
    valid: int
    index: int | None = None
    high: "Node | None" = None
    low: "Node | None" = None


def balanced(value: int, width: int) -> int:
    validate(value, width)
    padded = 1 << (width - 1).bit_length()

    def up(start: int, size: int) -> Node:
        if size == 1:
            return Node((value >> start) & 1, index=start)
        low = up(start, size // 2)
        high = up(start + size // 2, size // 2)
        return Node(high.valid | low.valid, high=high, low=low)

    def down(node: Node, blocked: int) -> int:
        if node.index is not None:
            return (node.valid & (1 - blocked)) << node.index
        assert node.high is not None and node.low is not None
        return down(node.high, blocked) | down(node.low, blocked | node.high.valid)

    return down(up(0, padded), 0)


def abstract_bounds(width: int) -> dict[str, int]:
    """Conservative counts, two-input OR/AND/NOT unit gates, free wires.

    Both counts include unoptimized constant operations. These are topology
    bounds, not measured silicon or FPGA timing, area or synthesized counts.
    """
    if width < 1:
        raise ValueError("positive width required")
    height = (width - 1).bit_length()
    padded = 1 << height
    return {"padded_width": padded, "tree_height": height,
            "serial_depth_upper": width + 1, "balanced_depth_upper": 2 * height + 2,
            "balanced_gate_upper": 4 * padded - 2}
