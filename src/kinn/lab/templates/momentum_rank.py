"""12-1 momentum: each day buy the strongest large stocks of the past year, skipping a month."""

# Ranking mode: signal() returns a score; the Lab buys the top N scores each day.

SETTINGS = {
    "universe": {"min_market_cap": 2e9, "min_dollar_volume": 5_000_000, "min_price": 5},
    "entry": {"mode": "rank", "top_n": 2, "rank_order": "highest"},
    "exit": {"hold_days": 21},
    "book": {"position_size": 5000, "max_positions": 20},
}


def signal(data):
    price = data.adj_close
    return price.shift(21) / price.shift(252) - 1
