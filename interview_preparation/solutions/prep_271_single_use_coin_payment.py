"""Minimum exact payment from a supplied physical-coin inventory.

Each list index is one physical coin and may appear at most once. Coin values
are positive integers. Equal denominations at different indices are allowed.
Return indices of a minimum-cardinality subset, or None when impossible.
No denomination set or availability is invented from the original prompt.
"""


def minimum_payment_indices(coins, target=120):
    if type(target) is not int or target < 0:
        raise ValueError("target must be a nonnegative integer")
    if any(type(value) is not int or value <= 0 for value in coins):
        raise ValueError("physical coins must have positive integer values")
    n = len(coins)
    impossible = n + 1
    # Keep prior rows immutable so backtracking cannot accidentally reuse a coin.
    rows = [[0] + [impossible] * target]
    for value in coins:
        prior = rows[-1]
        current = prior.copy()
        for amount in range(value, target + 1):
            current[amount] = min(prior[amount], prior[amount - value] + 1)
        rows.append(current)
    if rows[n][target] == impossible:
        return None
    result = []
    amount = target
    for count in range(n, 0, -1):
        if rows[count][amount] != rows[count - 1][amount]:
            result.append(count - 1)
            amount -= coins[count - 1]
    assert amount == 0
    result.reverse()
    return result
