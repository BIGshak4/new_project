"""A fully supplied physical-coin instance, explicitly chosen for teaching.

COINS contains one physical coin at each index; 60 cannot be used twice.
The supplied screenshot did not supply this inventory.
"""
COINS = (100, 60, 35, 25, 15, 10)
TARGET = 120


def minimum_indices(coins, target):
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    if any(type(value) is not int or value <= 0 for value in coins):
        raise ValueError("coin values must be positive integers")
    count = len(coins)
    unreachable = count + 1
    rows = [[0] + [unreachable] * target]
    for value in coins:
        previous = rows[-1]
        current = previous.copy()
        for amount in range(value, target + 1):
            current[amount] = min(previous[amount], previous[amount - value] + 1)
        rows.append(current)
    if rows[-1][target] == unreachable:
        return None
    result, amount = [], target
    for i in range(count, 0, -1):
        if rows[i][amount] < rows[i - 1][amount]:
            result.append(i - 1)
            amount -= coins[i - 1]
    assert amount == 0
    return list(reversed(result))


def completed_payment():
    return minimum_indices(COINS, TARGET)
