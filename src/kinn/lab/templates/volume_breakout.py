"""Volume breakout: a new 50-day high on three times the usual dollar volume."""

SETTINGS = {
    "universe": {"min_market_cap": 300e6, "min_dollar_volume": 1_000_000},
    "exit": {"hold_days": 20, "stop_loss": 0.10},
}


def signal(data):
    close = data.close
    high_50 = close.rolling(50).max().shift(1)  # the high of the 50 sessions before today
    usual = data.dollar_volume.rolling(20).mean().shift(1)
    return (close > high_50) & (data.dollar_volume > 3 * usual)
