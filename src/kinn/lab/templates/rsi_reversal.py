"""Short-term reversal: RSI(2) under 10 in a stock above its 200-day average."""

# Sells at the next open after a close above the 5-day average (exit_signal), or after 10 days.

SETTINGS = {
    "universe": {"min_market_cap": 2e9, "min_dollar_volume": 5_000_000, "min_price": 5},
    "exit": {"hold_days": 10, "stop_loss": 0.10},
}


def rsi(close, days):
    change = close.diff()
    up = change.clip(lower=0).ewm(alpha=1 / days, adjust=False).mean()
    down = (-change.clip(upper=0)).ewm(alpha=1 / days, adjust=False).mean()
    return 100 - 100 / (1 + up / down)


def signal(data):
    close = data.adj_close
    return (rsi(close, 2) < 10) & (close > close.rolling(200).mean())


def exit_signal(data):
    close = data.adj_close
    return close > close.rolling(5).mean()
