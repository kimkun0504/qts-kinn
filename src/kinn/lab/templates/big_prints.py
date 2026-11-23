"""Big prints: a quiet up day traded in pieces three times the stock's normal size."""

# The lead of 18 November (strategies/big_prints): a fund building a position trades in
# larger pieces than the crowd. Buy the next open, hold 20 sessions.

import numpy as np

SETTINGS = {
    "universe": {
        "min_market_cap": 50e6,
        "max_market_cap": 300e6,
        "min_price": 2,
        "min_dollar_volume": 250_000,
    },
    "exit": {"hold_days": 20},
    "book": {"position_size": 2000, "max_positions": 10},
}


def signal(data):
    size = data.trade_size  # shares per trade
    normal = np.exp(np.log(size).rolling(60).mean().shift(1))  # geometric mean, last 60 days
    footprint = size / normal

    heavy = data.dollar_volume >= 1.5 * data.adv20  # 1.5x the usual dollar volume
    quiet_up = (data.returns >= 0) & (data.returns <= 0.04)  # up, but not a news jump
    no_8k = ~data.filing.rolling(5, min_periods=1).max().astype(bool)  # no 8-K this week

    buy = (footprint >= 3) & heavy & quiet_up & no_8k

    # Skip index days: when 5% or more of the universe trades in large pieces at once.
    eligible = data.eligible
    share = ((footprint >= 2) & eligible).sum(axis=1) / eligible.sum(axis=1).clip(lower=1)
    buy[share >= 0.05] = False
    return buy
