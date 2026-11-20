"""Weekly reversal, long and short: buy last week's biggest losers among large stocks and short
the biggest winners, holding five days."""

SETTINGS = {
    "universe": {"min_market_cap": 2e9, "min_dollar_volume": 10_000_000, "min_price": 5},
    "entry": {"mode": "rank", "top_n": 2, "rank_order": "lowest", "side": "both"},
    "exit": {"hold_days": 5},
    "book": {"position_size": 5000, "max_positions": 10, "borrow_rate": 0.01},
}


def signal(data):
    price = data.adj_close
    return price / price.shift(5) - 1
