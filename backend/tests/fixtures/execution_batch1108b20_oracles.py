"""Independent string/list/deque oracles; no candidate imports."""
from collections import deque


def cursor_oracle(operations):
    values, current, output = [], 0, []
    for operation in operations:
        name, *args = operation
        if name.startswith("insert_"):
            if not values:
                values.append(args[0])
            elif name == "insert_before":
                values.insert(current, args[0])
                current += 1
            else:
                values.insert(current + 1, args[0])
            result = None
        elif name.startswith("move_"):
            direction = -1 if name == "move_prev" else 1
            result = bool(values and 0 <= current + direction < len(values))
            if result:
                current += direction
        else:
            index = current + (-1 if name == "prev" else 1 if name == "next" else 0)
            if not values or not 0 <= index < len(values):
                output.append({"ok": False, "error": "empty_or_boundary"})
                continue
            result = values[index]
            if name == "delete":
                values.pop(current)
                current = max(0, min(current, len(values) - 1))
        output.append({"ok": True, "value": result})
    return output


def queue_oracle(operations):
    model, output = deque(), []
    for operation in operations:
        name, *args = operation
        if name == "enqueue":
            model.append(args[0])
            value = None
        elif name == "is_empty":
            value = not model
        elif not model:
            output.append({"ok": False, "error": "empty"})
            continue
        else:
            value = model.popleft() if name == "dequeue" else model[0]
        output.append({"ok": True, "value": value})
    return output


def remove_oracle(text):
    return text.replace(" ", "")


ORACLES = {"prep-remove-all-ascii-spaces": remove_oracle, "prep-cursor-list-using-two-stacks": cursor_oracle, "prep-fifo-queue-using-two-stacks": queue_oracle}
