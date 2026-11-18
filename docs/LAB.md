# The Lab: run your own algorithm on every stock

Open the Workbench (`uv run python -m apps.workbench`, then http://127.0.0.1:8321) and choose
**Lab** in the side rail. Write an algorithm, set the period and the rules, press **Run**
(⌘↵; ⌘S saves). The run goes through every stock in the universe you chose and shows what the
algorithm made, year by year and stock by stock. Why it is built this way: [decision 0023](decisions/0023-research-lab.md).

## An algorithm

An algorithm is a Python file with one required function, `signal(data)`:

```python
"""Volume breakout: a new 50-day high on three times the usual dollar volume."""


def signal(data):
    close = data.close
    high_50 = close.rolling(50).max().shift(1)  # the high of the 50 sessions before today
    usual = data.dollar_volume.rolling(20).mean().shift(1)
    return (close > high_50) & (data.dollar_volume > 3 * usual)
```

- `data.close`, `data.dollar_volume` and every other field are **pandas DataFrames**: one row
  per session, one column per stock (labelled by ticker). Use any pandas or numpy you like.
- `signal` returns a DataFrame of the same shape. **`True` on a day means "buy at the next
  open".** Missing values and `False` mean nothing.
- The value on a row may use only that row and earlier rows (that day's close is known; the
  next day's is not). The Lab checks this on every run: it runs your code again on the data cut
  off at two dates, and if the signals up to a cut-off change, the run is marked **The code
  looks ahead**, with the first stock and day that changed. The usual causes are a
  `shift(-1)`, a centered rolling window, or a statistic over the whole column
  (`close.mean()`, `rank(pct=True)` down the dates).
- Each `data.<field>` gives you your own table: change it as you like (pandas copies it on the
  first change, so the data underneath and your other tables stay as they were).
  `.to_numpy()` on one is read-only; use `.to_numpy(copy=True)` to write into the array.

Optional parts:

```python
def exit_signal(data):
    """True where an open position should be sold at the next open."""
    return data.close < data.close.rolling(10).mean()


SETTINGS = {  # defaults for the settings panel; the panel can change them
    "universe": {"min_market_cap": 50e6, "max_market_cap": 300e6},
    "exit": {"hold_days": 20, "stop_loss": 0.15},
}
```

**Ranking mode.** Set *Entry* to *Top scores* and return numbers instead of `True`/`False`: each
day the Lab buys the N best-scored stocks (or the N lowest) among those it does not already
hold. NaN means no score. To hold a portfolio refreshed once a month, return scores only on the
first session of each month (NaN on the other days) and hold about 21 sessions.

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
`volume` runs much faster than one that reads everything. `data.fields()` lists them, and the
**Data** tab under the editor lists them with a search; click a name to put it in the code.
Typing `data.` in the editor offers them too.

Columns are the stocks that were in the universe on at least one day of the period, in the
order of their company id. A stock is `eligible` on a morning when the universe's filters pass
on the previous close and it traded within the last 10 calendar days (one back from a longer
halt waits a session).

## The rules every algorithm is held to

- **Entry:** the open of the session after the signal, if the stock is in the universe that
  morning and trades. One position per stock at a time: a signal while the stock is held is
  ignored; a new one may open the session after the exit.
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

## The settings panel

Under the editor. A blank box keeps the value from your code's `SETTINGS`, or the Lab's default
when the code sets none; that value shows greyed in the box. A typed value overrides it for
this run and is remembered for this algorithm in this browser. Market cap is in $M, dollar
volume in $K, the stop and the target in %. Typing 0 for the stop, the target or the largest
market cap turns it off. **Clear changes** goes back to the code's values. The settings a run
used are kept with it; **Use its settings** (on a past run's Code tab) puts them back.

The periods are the research's: 2010–2017 to search, 2005–2009 and 2018–2022 to test, 2023 to
13 October as a check, or all of them. A custom period takes any dates from 2005-01-01 to
2023-10-13 (the last day a position may open; exits run on to 2023-11-08).

## Reading a result

- **Summary:** trades, the average and median trade after costs, the share that made money,
  the weekly t (the average of each week's trades over its spread; over 3 is the research's
  bar), years positive, the book's profit, worst drawdown and return on the money tied up.
- **Overview:** the summary, the book's profit beside SPY on the same capital, the best and
  worst stocks, the spread of trade returns and how trades ended.
- **Stocks:** every stock that traded, best to worst or worst to best, with a search and a
  sector filter; every column sorts. *Profit* counts every trade at the position size (what
  the signal made on that stock); *In the book* counts only the trades the book had room for.
  Click a stock for its trades.
- **Trades:** every trade, sorted and filtered by stock and by whether the book took it;
  **Download all as CSV** for your own analysis.
- **Years**, and **Code**: the code and settings the run used.
- **Runs of this algorithm**, with its **trial count**: the runs that got as far as computing
  signals (a run that stops on a syntax error is not a trial). Ten tries that each look at the
  same years make the best of them less trustworthy; hold the 2018–2022 test years back until
  the idea is settled.

One run goes at a time; **Cancel** stops it. A run that stops on an error shows it with the
line of your code where it happened.

## How big a run can be

A run holds about 40 bytes per stock per session before the fields your code adds. All years
(about 5,000 sessions with the warm-up) over a $50M-and-up universe (about 9,500 stocks) needs
about 2 GB plus what your code makes, and takes seconds. The Lab refuses a run that would need
more than 60% of the machine's memory and says how big it was; narrow the universe or the
period.

## Where things are kept

`KINN_LAB_DIR` (default `lab/` beside the run store): `algorithms/<name>.py` (your files),
`trash/` (deleted algorithms, kept), `runs/<run_id>/` (a copy of the code and settings run,
progress, the worker's log, results: `summary.json`, `trades.parquet`, `by_stock.json`,
`by_year.json`, `equity.json`). Nothing in it is in git. Back the algorithms up, or move an idea that holds up into `strategies/` and the usual
protocol (`docs/NEW_STRATEGY.md`).
