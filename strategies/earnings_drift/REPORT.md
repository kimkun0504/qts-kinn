# Earnings drift ($50M to $300M): passed the holdout

Plan and the rule: [HYPOTHESIS.md](HYPOTHESIS.md). How the rule was found and tested before
the holdout: [`strategies/swing_search/REPORT.md`](../swing_search/REPORT.md).

## The holdout (2026-11-16, run by the owner)

Run `20261116T193948Z_human_earnings_drift_4e47e374`, config `holdout`, 2023-11-09 to
2026-11-06, on the unsealed build, at commit `f0c6c76`. One run. The owner's rehearsal on the
search years through the unsealed build printed the research run's figures exactly (833
trades, 3.56%).

| | Holdout | Search years (2010–2022) | 2005–2009 |
|---|---|---|---|
| Signals | 460 | 1,059 | 430 |
| Trades taken (10 positions of $2,000) | 266 | 833 | 343 |
| A trade, auction allowance (1×) | **5.04%** | 3.56% | 4.60% |
| A trade, allowance doubled (2×) | **4.67%** | 3.18% | 4.23% |
| A trade, modelled spread crossed | 3.91% | 2.39% | 3.46% |
| Median trade, winners | 1.0%, 52% | | |
| Total, 1× / 2× | $26,716 / $24,765 | $59,246 / $52,868 | $31,463 / $28,929 |
| Sharpe, 1× / 2× (booked on exit day) | 1.47 / 1.37 | 1.30 / 1.17 | 1.94 / 1.79 |
| Worst drawdown, marked daily | $6,784 | $8,880 | $9,734 |

**Verdict by the rule set before the run** (mean a trade at 2× of 1% or more and a positive
total at 2×): **passed.**

By year (1×): 2023 from 9 November, +7.3% (10 trades); 2024, +9.8% (85); 2025, +4.9% (87);
2026 to 6 November, +0.1% (84). Three things to keep in view:

- **2026 was flat.** 84 trades made nothing (−0.3% at 2×). Flat years have happened before
  (2011, 2022), and the rule's profit has always come from a few large winners, but the most
  recent year is the weakest of the three.
- **2024 carries the total:** $16,581 of the $26,716.
- **Signals came almost twice as often** as before the seal (about 150 a year against 80),
  so the 10-position book skipped 182 of 460. The skipped signals are not in the run's
  files; the per-trade figures are for the trades taken, chosen by volume.

The holdout is now spent for the family `swing_search`.

## Fills, measured from ticks (2026-11-16)

150 trades of 2015 to 2023 at random; quotes and trades around the open of the entry day and
the close of the exit day (`research/claude/swing_fill_measure.py`; plan in HYPOTHESIS.md).

| | Under $1M a day (93 trades) | $1M a day and over (57) |
|---|---|---|
| Opening cross printed | 99% | 100% |
| Closing cross printed | 88% | 100% |
| A cross on both sides | 87% | 100% |
| Dollars in the opening / closing cross, median | $36,000 / $27,000 | $115,000 / $93,000 |
| The same, smallest tenth | $3,500 / $2,400 | $30,000 / $10,000 |
| Opening cross against the midpoint 30 s later | +0.08% | +0.20% |
| Closing cross against the midpoint 30 s earlier | −0.02% | +0.03% |
| Market order instead, both sides, against the bar's prices | 1.61% | 0.52% |
| Modelled spread crossed, both sides | 2.0% | 0.86% |

- **The bar's open and close are auction prints.** The cross price is the bar's price in 86%
  of entries and 96% of exits.
- **The auction price is fair.** A buyer in the opening cross pays about 0.1% more than the
  midpoint half a minute later; a seller in the closing cross gives up nothing. The auction
  allowance (0.50% a round trip under $1M a day, 0.20% above) is larger than this under $1M
  and about equal to it above.
- **Market orders cost less than modelled:** 1.2% a round trip on average, against the 1.6%
  the "spread crossed" column assumes. Most of it is the entry: the quote is wide just after
  the open (half-spread 1.3% under $1M a day) and narrow before the close (0.3%).
- **Limits.** One exit in eight under $1M a day had no closing cross; there an on-close
  order does not fill and the position has to be sold in the market before the close. In a
  tenth of trades the cross is about the size of a $2,000 order, and such an order would
  move it. The ticks cannot show by how much.

By the rule written before reading the ticks (a cross on both sides in nine trades of ten,
and the cross within the allowance of the midpoint), **the auction allowance stands**: 92% of
trades have both crosses, and the cross costs 0.06% a round trip under $1M a day and 0.23%
above. This is not a `kinn fill-check` run, so the Workbench does not show fills as confirmed.

## The engine reproduces the research

`kinn swing` finds the same trades as the research scripts: of the 1,488 research trades of
2005 to 2022, 1,479 are found with gross returns equal to 15 decimal places. The nine it
drops are stocks back from a halt or relisting, which the rule excludes; one trade is added
at the 15% boundary by rounding. Runs `…_71f5b45c` (`research`) and `…_f50069e4` (`early`).

## Against the targets of decision 0017, on the holdout

| Target | Result |
|---|---|
| Net a trade of +1.0% at 2× | 4.67% |
| Sharpe above 1 | 1.37 at 2× (trades booked on the exit day) |
| Drawdown under half the account | $6,784 of $20,000, marked daily |
| Fills confirmed | Measured from ticks as above; not yet traded live |

## Paper trading (decision 0021)

`tools/owner/paper_earnings_drift.py`, run by the owner each evening after the close, finds
the day's signals from live data, fills the previous day's at the open, closes what has been
held 15 sessions at the close, and writes `paper/earnings_drift/report.md` with the next
morning's buys and the next close's sells. It keeps a 10-position and a 20-position book,
the same two with the quality test applied (below), and follows every signal. It sends no
order.

## The quality test (rule A50Q, 2026-11-16): found after the holdout, not yet proven

Some years of A50 are flat. The study in
[swing_search's report](../swing_search/REPORT.md#the-flat-years-which-signals-fail-after-the-holdout-on-signals-of-2005-to-october-2023)
found where the flat years come from: signals in companies that hold net cash and whose
stock is down over the past year make nothing. **A50Q** is A50 that takes a signal only if
the stock is up over the past 250 sessions or the company's debt is above its cash (plan:
HYPOTHESIS.md, addendum of 2026-11-16 23:30 ET).

The runner (`skip_fallen_cash_rich: true`) on the years already read, 10 positions, $20,000:

| Run | Trades | A trade | Doubled | Spread crossed | Total | Kept signals, before costs | Skipped |
|---|---|---|---|---|---|---|---|
| `early_quality`, 2005–2009 | 277 | 5.65% | 5.27% | 4.49% | $31,208 | 321 at 6.18% | 109 at 2.20% |
| `research_quality`, 2010–2022 | 711 | 4.27% | 3.89% | 3.09% | $60,672 | 805 at 5.03% | 254 at 1.44% |
| `check_quality`, 2023 to 8 Nov | 45 | 6.41% | 6.02% | 5.23% | $5,753 | 57 at 8.24% | 14 at −2.41% |

Every calendar year from 2005 to 2023 is positive at the allowance and at twice the
allowance; the lowest are 2008 ($1,316) and 2011 ($1,465), then 2017 ($2,106). Rule A50's
lowest on the same runner was 2011 at about nothing. The runner keeps 1,183 signals where
the research script kept 1,177; the difference is the same handful of boundary cases as
before. Runs `…_2df743f9`, `…_36506558`, `…_092e060e`.

**This is not proof.** The test was found on these same years. The holdout was spent on A50
before the test existed. Two things can still test it: the paper ledger, which now keeps two
more books that apply it (`ten_quality`, `twenty_quality`), and, if the owner decides, one
run of `holdout_quality` read by the terms the addendum sets.

In the paper ledger the two facts come from live sources: the year's return from the
vendor's daily bars, and cash less debt from the SEC's XBRL company facts (cash and
equivalents, less borrowings and lease liabilities, at the last 10-Q or 10-K filed before
the signal). These approximate Sharadar's fields rather than copy them, so each signal
records the figures used, and the report says for every signal whether it passed and why.
Signals already in the ledger get their facts on the next run; the new books start empty
and take signals from then on.

**One season nobody had looked at (autumn 2004).** The earnings item exists in the events
table from 23 August 2004 and every study began in 2005, so the season of October and
November 2004 was unseen by any rule here. Run once (`autumn_2004_quality`, run `…_4f729bcf`,
plan in the addendum of 23:59 ET): 33 signals; the 19 kept made 12.8% each before costs
and the 14 skipped 7.2%; the book took 17 trades at 12.57% each, $4,263 ($4,077 at doubled
costs). By the reading set beforehand that is **consistent**, and no more than that: late
2004 was a strong market for small stocks, 14 skipped signals are too few to say the test
added anything, and six of them were skipped only because the prices did not yet reach back
a year. Of the 19 kept, 15 made money. For rule A50 itself it is one more unseen season that made money.

A fifth book, `ten_quality_trend`, applies the quality test and leaves by the 20-day-average
exit (sell at the next open once a close is under the stock's 20-day exponential average,
30 sessions at most). On the years already read that book has the lowest drawdown of those
resting on tests set beforehand ($7,601 against $10,366; $5,783 a year, Sharpe 1.30). The
ledger's version of the exit gave the same exit day and return as the research's on 220
real signals.

## What the forward test can and cannot tell (2026-11-17)

From the spread of the 1,551 past trades (mean 3.9% a trade, standard deviation 23%; no new
rule is measured here).

- **The frozen rule can be read in about a year, not in weeks.** At the past mean, 137
  signals put the average two standard errors above zero; the ledger follows every signal
  and the holdout years had about 150 a year. If the edge is intact, a year of signals
  averages below zero about 1 time in 100 and below +2% about 1 in 7. A month or two of
  paper trading checks the plumbing (signals, fills, the nightly run), not the edge.
- **A bad start is ordinary.** Of all runs of 24 consecutive past signals, 21% averaged below
  zero and 8% below −3%; the worst averaged −22% (January 2020). After a run under −3% the
  next 24 averaged +6.7%. The ledger's first 24 signals (October–November 2026) are down a
  few percent with most still open.
- **Neither remaining test can settle the quality test.** It skips 24% of signals; in the
  past those made 0.8% a trade against 4.9% for the rest, a gap of 4.1 points. One run on
  the holdout (about 111 skipped signals) would measure that gap to ±2.2 points; a year of
  paper to ±3.9; three years to ±2.3. Even if the gap is as large as it was, none of these
  reaches two standard errors. The holdout run would be suggestive at best, and it is the
  most informative single look available.
- **So the choice between A50 and A50Q is a judgment about cost, not a test to wait for.**
  If the filter is right, it removes a quarter of the trades that made nothing and both
  losing-year risks. If it is wrong, it gives up a quarter of the profit. It cannot make the
  book worse by more than that.

## How much of the account it uses (2026-11-17)

Counted day by day on 2006 to October 2023, the 10-position book of A50Q holds **3.3
positions on average, a third of the account**. It is full on 5% of days and empty on 16%.
Signals come with the reporting seasons: about six positions in February–March, May, August
and November, one or two in between. With the 20-day-average exit it holds 4.2.

Would fewer, larger positions use the money better? $20,000, A50Q, the most volume first.
4 trials (5 and 7 positions, two exits). Code: `research/claude/swing_overnight.py` (`run_book`).

| Positions | Each | Exit | A year | Sharpe | Worst drawdown | Worst year | Losing years | Spread crossed, a year |
|---|---|---|---|---|---|---|---|---|
| 10 | $2,000 | 15 sessions | $5,097 | 1.13 | $10,366 | +$1,929 | 0 | $3,808 |
| 7 | $2,857 | 15 sessions | $6,298 | 1.10 | $14,487 | +$740 | 0 | $4,726 |
| 5 | $4,000 | 15 sessions | $7,043 | 0.96 | $20,486 | −$1,133 | 2 | $5,234 |
| 10 | $2,000 | 20-day average | $5,783 | 1.30 | $7,601 | +$1,161 | 0 | $4,529 |
| 7 | $2,857 | 20-day average | $6,692 | 1.24 | $10,408 | −$603 | 1 | $5,216 |
| 5 | $4,000 | 20-day average | $7,901 | 1.18 | $11,968 | −$2,470 | 2 | $6,248 |

- **Larger positions buy dollars with risk, one for one.** Seven positions make 16% to 24%
  more a year and the drawdown grows 37% to 40%; five make 37% to 38% more and the drawdown
  of the plain exit reaches the whole account. The Sharpe ratio falls at every step. The
  idle money is the price of the signals arriving together: a book sized for the busy weeks
  is mostly empty in the quiet ones.
- **Only the 10-position book with the 20-day exit keeps the drawdown under half the
  account** (decision 0017). Seven positions with that exit is just over ($10,408).
- **The idle cash can earn interest at no risk to the rule.** About $13,400 sits unused on
  average ($11,600 with the 20-day exit). In Treasury bills at 4% that is roughly $500 a
  year, a tenth more profit; at the near-zero rates of 2010 to 2021 it was nothing.

**Larger only while the book is nearly empty** (4 more trials; `research/claude/swing_sizing.py`).
A position of $4,000 while fewer than three are open, $2,000 after, never more invested than
the account: $6,241 a year with a drawdown of $13,696 on the plain exit, and $6,253 with
$8,577 on the 20-day exit (Sharpe 1.20, no losing year on the auction basis, one with the
spread crossed). More dollars, deeper drawdown again, so it does not pass the bar set for
it. "While fewer than five are open" is the 5-position book under another name.

Nothing here changes the paper books. The count is the owner's choice between dollars and
drawdown, made on years already read.

## What it is not yet

It has not traded. There is no broker connection, and the live sources (Massive for market
value, the SEC for 8-K items) differ from the research's (Sharadar), so the first weeks of the
paper ledger are also a check that the signals come out the same.
