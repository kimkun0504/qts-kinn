# Opening gap continuation report

**Verdict: park.** The single registered variant cleared the development event-count bar
with 8,483 events, then failed the cost bar. Buying after the opening confirmation earned
**+0.08% per event at 1× slippage and −0.13% at 2×** through the close. Even before costs,
the mean was +0.37%. The preregistered gate ended the experiment at the event-study stage.
The portfolio backtest and the 2017-01-03 to 2023-11-08 validation are unrun. The +3.00%
validation target, trade-count and daily t-statistic floors, and portfolio drawdown cap
remain untested.

## Development result

The [preregistration](HYPOTHESIS.md) was committed as `6a85bd7` before the first run. The
Workbench study entry records one completed, clean trial for this new family.

| Run | Config | Period | Data build | Run commit |
|---|---|---|---|---|
| `20261116T002542Z_gpt_opening_gap_continuation_9db697d9` | `development --study` | 2003-09-10 to 2016-12-30 | `6453bd3ec8` | `f43bce90` |

The study used the registered $2,000 target order size and IBKR Pro tiered cost model. It
measured each of the 8,483 events through the official close. Its mean round-trip charge
at 1× was 29 bps, including 20 bps of modelled slippage. Both day-clustered confidence
intervals include zero.

| Close horizon | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net return per event | +0.08% | −0.13% |
| 95% day-clustered interval | −0.31% to +0.48% | −0.51% to +0.27% |
| Summed event P&L | +$12,783 | −$21,421 |
| Daily event P&L t-statistic | +0.38 | −0.63 |
| Worst end-of-day drawdown of summed event P&L | −$30,480 | −$37,073 |

The dollar statistics use the stored per-event return after costs times entry price times
shares. P&L is summed by date across the manifest's 3,352 sessions, with zeros on days
without events. Drawdown is measured from the preceding cumulative P&L high, including the
starting balance. Every event enters this series independently, even when orders overlap
or exceed the intended $20,000 buying power. The drawdowns describe that unconstrained
series and cannot be used as estimates of account drawdown. Portfolio trade counts are
unavailable.

## Development by year

| Year | Events | Net/event at 1× | Net/event at 2× | Event P&L at 1× | Event P&L at 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 72 | +0.30% | +0.07% | +$416 | +$100 |
| 2004 | 393 | +0.17% | −0.05% | +$1,300 | −$431 |
| 2005 | 406 | +0.71% | +0.50% | +$5,683 | +$3,987 |
| 2006 | 437 | −0.06% | −0.26% | −$512 | −$2,251 |
| 2007 | 577 | −0.17% | −0.36% | −$1,923 | −$4,208 |
| 2008 | 1,660 | +0.08% | −0.14% | +$2,822 | −$4,664 |
| 2009 | 1,016 | +0.31% | +0.11% | +$6,285 | +$2,187 |
| 2010 | 664 | −0.36% | −0.56% | −$4,833 | −$7,364 |
| 2011 | 635 | +0.40% | +0.22% | +$5,083 | +$2,774 |
| 2012 | 445 | +0.01% | −0.18% | +$65 | −$1,557 |
| 2013 | 423 | +0.05% | −0.14% | +$427 | −$1,172 |
| 2014 | 556 | −0.13% | −0.32% | −$1,446 | −$3,564 |
| 2015 | 518 | +0.16% | −0.04% | +$1,594 | −$412 |
| 2016 | 681 | −0.16% | −0.36% | −$2,179 | −$4,847 |

## Platform and data

- The event study assigned entry prices to 54 events after order expiry. The portfolio engine
  would leave those orders unfilled. The [change request](../../docs/requests/2026-11-15-validation-event-study-expiry.md)
  documents the discrepancy. The verdict uses the original study output.
- The study approximates both sides' execution costs using the entry bar. It would need
  exit-side prices and liquidity for an independent estimate of closing execution costs.
  About 10% of study entries exceed the portfolio engine's 5% participation ceiling.
- The stored run passed lookahead replay on all 2,467 signal sessions. Synthetic tests
  also cut the session just before and at confirmation, and cover next-bar execution,
  order expiry, partial fills and flattening on early closes.
- The absence of historical quotes and halt flags limits the market-fill and cost model.
  The prior close can be stale following a trading interruption, and imperfect corporate
  action records can make a price gap look like buying. The screen yielded too little net
  return to justify chasing those cases or tuning to an annual subset.
