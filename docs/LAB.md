# The Lab: run your own algorithm on every stock

Open the Workbench (`uv run python -m apps.workbench`, then http://127.0.0.1:8321) and choose
**Lab** in the side rail. Write an algorithm, set the period and the rules, press **Run**. The
run goes through every stock in the universe you chose and shows what the algorithm made, year
by year and stock by stock. Why it is built this way: [decision 0023](decisions/0023-research-lab.md).

## An algorithm

An algorithm is a Python file with one required function, `signal(data)`:

```python
"""Volume breakout: a new 50-day high on three times the usual dollar volume."""

def signal(data):
    close = data.close
    high_50 = close.rolling(50).max().shift(1)          # the high of the 50 sessions before today
    usual = data.dollar_volume.rolling(20).mean().shift(1)
    return (close > high_50) & (data.dollar_volume > 3 * usual)
```

- `data.close`, `data.dollar_volume` and every other field are **pandas DataFrames**: one row
  per session, one column per stock (labelled by ticker). Use any pandas or numpy you like.
- `signal` returns a DataFrame of the same shape. **`True` on a day means "buy at the next
  open".** Missing values and `False` mean nothing.
- The value on a row may use only that row and earlier rows (that day's close is known; the
  next day's is not). The Lab checks this on every run: it runs your code again on the data cut
  off at two dates, and if the signals up to a cut-off change, the run is marked **uses future
  data**. The usual cause is a `shift(-1)` or a centered rolling window.

Optional parts:

```python
def exit_signal(data):
    """True where an open position should be sold at the next open."""
    return data.close < data.close.rolling(10).mean()

SETTINGS = {                  # defaults for the settings panel; the panel can change them
    "universe": {"min_market_cap": 50e6, "max_market_cap": 300e6},
    "exit": {"hold_days": 20, "stop_loss": 0.15},
}
```

**Ranking mode.** Set *Entry* to *Rank* and return numbers instead of `True`/`False`: each day
the Lab buys the top N stocks by score (or the bottom N) among those not already held.

```python
def signal(data):
    """12-1 momentum: the return over the last year, skipping the latest month."""
    return data.adj_close.shift(21) / data.adj_close.shift(252) - 1
```

## The data

Every field is a DataFrame (sessions × stocks) unless marked. Everything comes through the
platform's sealed data store: **nothing on or after 2023-11-09 can be read**.

| Field | What it is | Known |
|---|---|---|
| `open`, `high`, `low`, `close` | The day's prices, as traded that day | that day |
| `adj_close` | Close adjusted for splits; use it for returns across days | that day |
| `returns` | Close-to-close return, split-adjusted | that day |
| `volume` | Shares traded | that day |
| `dollar_volume` | Close × volume | that day |
| `transactions` | Number of trades (Massive day bars) | that day |
| `trade_size` | Shares per trade (volume ÷ transactions) | that day |
| `market_cap` | Market value at the previous close | before the open |
| `adv20` | Median dollar volume of the previous 20 sessions | before the open |
| `eligible` | In the universe you chose | before the open |
| `earnings` | A results 8-K (item 2.02) was filed that day | that day |
| `filing` | Any 8-K was filed that day | that day |
| `revenue`, `gross_profit`, `operating_income`, `net_income`, `operating_cash_flow`, `capex`, `free_cash_flow`, `eps`, `dividends_per_share` | As reported, trailing twelve months | the session after filing |
| `equity`, `assets`, `liabilities`, `debt`, `cash`, `shares`, `book_value_per_share` | As reported, latest quarter | the session after filing |
| `sector`, `industry`, `exchange`, `name` | One value per stock (pandas Series) | static |
| `spy` | SPY's close (Series by session) | that day |
| `universe_return` | Equal-weight average daily return of the eligible stocks (Series) | that day |

Fields load the first time your code uses them, so an algorithm that reads only `close` and
`volume` runs much faster than one that reads everything. `data.fields()` lists them.

## The rules every algorithm is held to

- **Entry:** the open of the session after the signal, if the stock is in the universe that
  morning and trades. One position per stock at a time.
- **Exit:** the first of: the close of the *hold*-th session; the stop (a gap through it fills
  at the open; touched intraday it fills at the stop); the target; your `exit_signal` (next
  open); the stock's last close if it stops trading. A stop and a target touched on the same
  day count as the stop.
- **Costs:** the platform's IBKR model on the real share count at your position size: commission
  and fees, the auction allowance at the open and close, the half-spread on stop and target
  fills. Every number is shown at 1× and 2× slippage; a result negative at 2× is marked fragile.
- **The book:** a fixed dollar amount a position and at most N open at once. When more signals
  come than there is room for, the Lab takes the highest scores (ranking mode) or the most
  traded stocks (signal mode) and lists the rest as skipped.
- **Over the average:** each trade is also measured against the equal-weight average of the
  universe over the same sessions, the figure the research reports.

## Reading a result

- **Summary:** trades, the average and median trade after costs, the share that made money,
  the weekly t (the average of each week's trades over its spread; over 3 is the research's
  bar), years positive, the book's profit, worst drawdown and return on the money tied up.
- **Stocks:** every stock that traded, best to worst by total; click one for its trades.
- **Trades**, **Years**, and the **Runs** of this algorithm with its **trial count**: the
  number of runs so far. Ten tries that each look at the same years make the best of them
  less trustworthy; hold the 2018–2022 test years back until the idea is settled.

## Where things are kept

`KINN_LAB_DIR` (default `lab/` beside the run store): `algorithms/<name>.py` (your files),
`runs/<run_id>/` (a copy of the code and settings run, progress, results). Nothing in it is in
git. Back the algorithms up, or move an idea that holds up into `strategies/` and the usual
protocol (`docs/NEW_STRATEGY.md`).
