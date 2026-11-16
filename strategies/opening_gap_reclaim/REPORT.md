# Opening gap reclaim

**Verdict: park.** Buying a first-rotation rebound after a large overnight gap down
returned **−0.58% net per event at 1× slippage and −0.85% at 2×**. The mean gross
return through the close was −0.20%. The [preregistered](HYPOTHESIS.md) development
gate calls for +1.00% at 2×, a positive lower confidence bound, and positive 2× mean
returns in both halves. The point estimates in the two halves were −0.72% and −0.98%.
The sample gate passed with 664 events on 520 sessions. The cost and stability gates
failed. The portfolio backtest and validation remain unopened.

Run `20261116T010956Z_gpt_opening_gap_reclaim_bf31e0c0` used the 2003-09-10 to
2016-12-30 development period, build `6453bd3ec8` and clean commit `be6515d5`. The
hypothesis was committed at `1458781`. This adds one trial to `intraday_rebound`,
taking the family to 49 at the time of reporting. The Workbench study records the
1× and 2× results, and replay passed on all 520 signal sessions.

| Close outcome | 1× slippage | 2× slippage |
|---|---:|---:|
| Net return per event | −0.58% | −0.85% |
| 95% day-clustered interval | −1.31% to +0.24% | −1.57% to −0.02% |
| Summed event P&L | −$7,744 | −$11,214 |
| Daily event P&L t-statistic | −1.50 | −2.20 |
| Worst end-of-day drawdown of summed event P&L | −$8,035 | −$11,242 |

The dollar series comes from the saved event returns and their whole-share notionals,
using the $2,000 target order size and IBKR Pro tiered cost model. It sums overlapping
hypothetical events by day and includes all 3,352 development sessions for the t-statistic
and drawdown. Capital and participation constraints apply only in the portfolio engine.
The dollar metrics describe the unconstrained series and portfolio trade counts and
drawdown remain unmeasured.

## Annual development results

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 8 | −2.11% | −2.32% | −$338 | −$372 |
| 2004 | 40 | −0.44% | −0.69% | −$347 | −$546 |
| 2005 | 34 | −2.50% | −2.77% | −$1,693 | −$1,873 |
| 2006 | 38 | −1.31% | −1.57% | −$991 | −$1,188 |
| 2007 | 44 | −0.64% | −0.86% | −$567 | −$760 |
| 2008 | 146 | +0.29% | −0.01% | +$831 | −$27 |
| 2009 | 41 | −0.06% | −0.36% | −$52 | −$295 |
| 2010 | 22 | −1.72% | −1.99% | −$756 | −$873 |
| 2011 | 24 | −2.35% | −2.65% | −$1,125 | −$1,265 |
| 2012 | 37 | +0.68% | +0.48% | +$506 | +$354 |
| 2013 | 34 | +1.50% | +1.26% | +$1,016 | +$852 |
| 2014 | 52 | −1.81% | −2.04% | −$1,895 | −$2,131 |
| 2015 | 78 | −1.66% | −1.94% | −$2,592 | −$3,016 |
| 2016 | 66 | +0.19% | −0.06% | +$258 | −$73 |

The study used the first later print even after expiry for one event. The registered
within-expiry sensitivity was −0.59% at 1× and −0.85% at 2× over 663 events on 520
sessions. Modelled costs use the entry bar for both sides. About 11% of events would have
needed a smaller or partial order under the participation setting. The pre-cost loss and
the expiry result both undermine the case for this particular entry. A fresh hypothesis
would need a measurable reason to distinguish temporary opening pressure from repricing
on adverse news, with the information observable at entry.
