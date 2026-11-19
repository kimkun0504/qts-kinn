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
**Data** tab beside the editor lists them with a search: click one for an example and a copy
button. Nothing in the Data tab writes into your code; typing `data.` in the editor offers every
field to pick from.

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

## Checks while you type

The Lab reads your code as you type (it never runs it to check it) and marks problems on the
line, with the count in the toolbar; click the count to go to the first one.

- **Errors** stop a run until they are fixed: a syntax error, no `signal(data)`, a `signal` or
  `exit_signal` that does not take one argument, a `SETTINGS` the Lab would refuse.
- **Warnings** do not: `data.<name>` that is not a field (with the nearest field named), a
  `shift` by a negative number or a centered rolling window (both read later days; the
  lookahead test would mark the run), an import of a helper module that is not in the library.

The server checks again when Run is pressed, so broken code never makes a run.

## History

Every save keeps the version before it (`lab/history/<name>/`, the last 200), and every run
keeps the exact code it ran. The **History** tab beside the editor lists the saved versions,
newest first; click one to see it and **Restore this version** to put it back in the editor
(⌘Z undoes that; Save keeps it). A helper module has the same History beside its editor.

## Helper modules (the library)

Functions several algorithms share go in a helper module: **Lab → Library → New helper
module**. A module called `helpers` is imported as `lab.helpers`:

```python
from lab.helpers import zscore


def signal(data):
    return zscore(data.returns.rolling(5).sum(), 60) > 2
```

Each run keeps a copy of the library as it was (`runs/<run_id>/pkg/lab/`), and its hash in the
manifest, so changing a module later never changes what an old run was. An error inside a
module names the module's line (`lab/helpers.py, line 7`).

## The settings panel

Beside the editor. A blank box keeps the value from your code's `SETTINGS`, or the Lab's default
when the code sets none; that value shows greyed in the box. A typed value overrides it for
this run and is remembered for this algorithm in this browser. Market cap is in $M, dollar
volume in $K, the stop and the target in %. Typing 0 for the stop, the target or the largest
market cap turns it off. **Reset** goes back to the code's values. The settings a run
used are kept with it; **Use its settings** (on a past run's Code tab) puts them back.

The periods are the research's: 2010–2017 to search, 2005–2009 and 2018–2022 to test, 2023 to
13 October as a check, or all of them. A custom period takes any dates from 2005-01-01 to
2023-10-13 (the last day a position may open; exits run on to 2023-11-08).

## Reading a result

- **Summary:** trades, the average and median trade after costs, the share that made money,
  the weekly t (the average of each week's trades over its spread; over 3 is the research's
  bar), years positive, the book's profit, worst drawdown and return on the money tied up.
- **Overview:** the summary; the book with a switch between its profit, its drawdown and its
  open positions; the best and worst stocks; profit by month; the spread of trade returns and
  how trades ended.
  - The profit view shows SPY two ways. *SPY all-in* puts the whole capital in SPY every day.
    *SPY matched* puts in SPY only the money the book had invested that day (open positions
    times the position size), so it is the fair comparison: a book that is a fifth invested
    should be judged against a fifth of SPY's moves on the same days.
  - **After the signal** is the average split-adjusted move of the traded stocks from the close
    of the signal day, beside the universe's, from 20 sessions before to well past the exit,
    with a 95% band around the average excess. A line still rising at the exit says a longer
    hold had more to give; one that peaks before it says the hold is too long.
- **How the scores sorted the stocks** (ranking mode only): each day the stocks the book could
  have bought are split into tenths by score, and each tenth's return from the next open over
  the hold is set against that day's average; the rank correlation of score and return (IC) is
  taken each day, with a t-stat on days a hold apart so returns do not overlap, and by year.
  Before costs. A ranking that works rises steadily across the tenths and keeps a positive IC in
  most years (`factor.json`).
- **Compare** (two finished runs or more): the summary side by side with the difference, the
  settings that differ, both profit curves, and what changed in the code.
- **Stocks:** every stock that traded, best to worst or worst to best, with a search and a
  sector filter; every column sorts. *Profit* counts every trade at the position size (what
  the signal made on that stock); *In the book* counts only the trades the book had room for.
  Click a row for its trades; click the ticker for the stock page (its chart with every trade
  any run made in it, opened at the company that held the ticker on the trade date).
- **Trades:** every trade, sorted and filtered by stock and by whether the book took it;
  **Download all as CSV** for your own analysis.
- **Years**, and **Code**: the code and settings the run used.
- **A note** on any run: why you tried it and what you made of it, shown above the results and
  in the list of runs (`note.txt`). Writing one does not change the run or its trial count.
- **Runs of this algorithm**, with its **trial count**: the runs that got as far as computing
  signals (a run that stops on a syntax error is not a trial). Ten tries that each look at the
  same years make the best of them less trustworthy; hold the 2018–2022 test years back until
  the idea is settled.

One run goes at a time; **Cancel** stops it. The toolbar shows how the last run ended, and
when a run you started ends the page moves to its results. A run that stops on an error shows
it with the line of your code where it happened. A run stops by itself after 30 minutes
(`KINN_LAB_TIME_LIMIT`, in minutes, before starting the Workbench; 0 for no limit); a `try` in
your code cannot hold it.

## How big a run can be

A run holds about 40 bytes per stock per session before the fields your code adds. All years
(about 5,000 sessions with the warm-up) over a $50M-and-up universe (about 9,500 stocks) needs
about 2 GB plus what your code makes, and takes seconds. The Lab refuses a run that would need
more than 60% of the machine's memory and says how big it was; narrow the universe or the
period.

**The cache.** The first run of a universe and period reads the prices from the data store and
keeps them in `lab/cache/`; the next run with the same universe and period (whatever the code)
reads them from there, memory-mapped, as it does the trade counts, filing days, fundamentals
and SPY once read. A run over 2010–2017 goes from about 4 seconds to 1; all years over 9,500
stocks from 9 to 3. The cache holds at most 6 GB (`KINN_LAB_CACHE_GB`), dropping what was used
longest ago; a new data build starts it afresh. Deleting the folder is always safe.

How long each stage of a run took is in its `summary.json` (`timings`) and its `log.txt`.

## Sweeps

To see how much a result depends on one setting, pick it under **Sweep** in the settings panel
(hold, stop loss, take profit, max open positions, or stocks a day in ranking mode) and give 2 to
12 values (`5, 10, 20, 40`; `none` for no stop or target). Run then tries each value on the
**same signals and the same costs**, so only that setting changes, and the results show a bar
for each value and a table of every measure; this run's own value is marked.

**Each value counts as a trial** (and the run's own setting too, if it is not among them): ten
holds tried are ten trials, and the best of them is less trustworthy than any one alone. Prefer a
setting whose neighbours do nearly as well. From the terminal: `--sweep exit.hold_days=5,10,20`.

## The command line

The same runs without the page, from the repo folder:

```bash
uv run kinn lab list                                   # algorithms, trials, last result
uv run kinn lab run momentum_rank --period search      # an algorithm in the Lab folder
uv run kinn lab run ~/ideas/gap_fade.py --start 2012-01-03 --end 2016-12-30
uv run kinn lab run gap_fade --settings '{"exit": {"hold_days": 5, "stop_loss": 0.1}}'
uv run kinn lab selfcheck                              # every template on 2015, in a scratch folder
```

A run from the command line is saved, counted and shown on the page like any other. `selfcheck`
runs every template and a deliberate peek in a temporary folder (your algorithms and trial
counts are untouched) and says whether everything behaved: use it after an update.

## Where things are kept

`KINN_LAB_DIR` (default `lab/` beside the run store): `algorithms/<name>.py` (your files),
`library/<name>.py` (helper modules), `trash/` (deleted files, kept), `cache/` (prices between
runs), `runs/<run_id>/` (a copy of the code, the library and the settings run, progress, the
log, results: `summary.json`, `trades.parquet`, `by_stock.json`, `by_year.json`,
`equity.json` (with `spy_matched` from 2026-11-19), `path.json` and, in ranking mode,
`factor.json`, for a sweep `sweep.json` (from 2026-11-19), and `note.txt` if you wrote a
note on the run). Runs from
before 2026-11-19 have no signal path and show SPY all-in only; run them again to see both. Nothing in it is in git. Back the algorithms up, or move an idea that holds up into `strategies/` and the usual
protocol (`docs/NEW_STRATEGY.md`).
