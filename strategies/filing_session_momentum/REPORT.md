# Filing-session momentum

**Verdict: park.** A large first-hour gain after a near-flat open and a prior-session
8-K returned **−0.16% net per event at 1× slippage and −0.37% at 2×**. The +0.15%
gross mean could not cover the 0.31% modelled round-trip charge at 1×. The sample passed
with 2,045 events across 1,064 sessions. The 2× mean missed the preregistered +1.00%
bar, the lower confidence bound was negative, and both development halves lost at 2×
(−0.29% and −0.46% per event). This was the second and last candidate in the
[preregistered slate](HYPOTHESIS.md). Neither candidate earned a portfolio backtest or
validation run. The +2% research target and +3% stretch target remain unverified.

Run `20261116T011225Z_gpt_filing_session_momentum_8458ec00` used the 2003-09-10 to
2016-12-30 development period, build `6453bd3ec8` and clean commit `aeb3fc21`. The
hypothesis was committed at `1458781`, before either study. This was the sole trial in
`filing_session_momentum`. The Workbench study records the 1× and 2× results, and
replay passed on all 1,064 signal sessions.

| Close outcome | 1× slippage | 2× slippage |
|---|---:|---:|
| Net return per event | −0.16% | −0.37% |
| 95% day-clustered interval | −0.41% to +0.10% | −0.62% to −0.11% |
| Summed event P&L | −$6,475 | −$15,098 |
| Daily event P&L t-statistic | −1.23 | −2.88 |
| Worst end-of-day drawdown of summed event P&L | −$7,779 | −$16,095 |

The dollar series uses stored event returns and identical whole-share notionals under
both costs. The $2,000 target applies to each event, with overlapping events summed
across all 3,352 development sessions. The event study ignores the $20,000 portfolio
budget and participation limit, so these drawdowns describe only the summed event series.
Portfolio trade counts and drawdown remain unmeasured.

## Annual development results

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 25 | −0.08% | −0.28% | −$41 | −$140 |
| 2004 | 57 | −0.26% | −0.48% | −$298 | −$553 |
| 2005 | 74 | −0.89% | −1.12% | −$1,311 | −$1,651 |
| 2006 | 81 | −0.31% | −0.54% | −$502 | −$868 |
| 2007 | 113 | −0.27% | −0.48% | −$600 | −$1,078 |
| 2008 | 368 | −0.08% | −0.29% | −$594 | −$2,109 |
| 2009 | 290 | +0.32% | +0.12% | +$1,832 | +$674 |
| 2010 | 95 | +0.09% | −0.13% | +$170 | −$250 |
| 2011 | 132 | −0.46% | −0.68% | −$1,213 | −$1,788 |
| 2012 | 95 | +0.12% | −0.09% | +$234 | −$166 |
| 2013 | 111 | −0.31% | −0.53% | −$697 | −$1,161 |
| 2014 | 128 | +0.05% | −0.17% | +$137 | −$424 |
| 2015 | 195 | −0.39% | −0.60% | −$1,490 | −$2,311 |
| 2016 | 281 | −0.38% | −0.59% | −$2,102 | −$3,274 |

## Execution and interpretation

The study ignores order expiry and measured one event whose first available print
occurred after expiry. Restricting to the registered order window gave −0.16% at 1×
and −0.37% at 2× for 2,044 events on 1,064 sessions. The model uses entry-bar inputs
for both costs. About 33% of study events exceeded participation on the entry bar
at the target size, which the portfolio engine would subject to partial fills.

The results reject this dated-filing rule as a screen for intraday continuation at
the registered costs. An 8-K count identifies neither the news that moved the stock
nor when the market first learned it. A timestamped disclosure and verified price
reaction would support a new test of news-driven continuation. A threshold change
on the same proxy would be another development trial.
