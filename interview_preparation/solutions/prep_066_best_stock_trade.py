"""One optional or mandatory trade; zero-based days and stable earliest ties.

Input contract: a sequence of nonnegative exact integer prices. Validation is
outside this algorithm. Return (buy_day, sell_day, profit), or None.
"""


def best_trade(prices, *, mandatory=False):
    if len(prices) < 2:
        return None
    low_day = 0
    best = None
    for sell in range(1, len(prices)):
        profit = prices[sell] - prices[low_day]
        if (mandatory or profit > 0) and (best is None or profit > best[2]):
            best = (low_day, sell, profit)
        # Strictly smaller preserves the earliest day at equal prices.
        if prices[sell] < prices[low_day]:
            low_day = sell
    return best
