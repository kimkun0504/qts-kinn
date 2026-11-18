"""Results jump: up 15% or more over two days on a results 8-K, on five times the usual volume."""

# In the spirit of rule A50 (strategies/earnings_drift), not the exact rule.

SETTINGS = {
    "universe": {"min_market_cap": 50e6, "max_market_cap": 300e6},
    "exit": {"hold_days": 15},
}


def signal(data):
    two_days = data.adj_close / data.adj_close.shift(2) - 1
    results = data.earnings | data.earnings.shift(1, fill_value=False)
    volume = (data.dollar_volume + data.dollar_volume.shift(1)) / 2
    return results & (two_days >= 0.15) & (volume >= 5 * data.adv20.shift(1))
