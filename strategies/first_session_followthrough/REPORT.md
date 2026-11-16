# First-session follow-through

**Verdict: park.** The closing-horizon study produced 218 events
on 202 dates, with 91 on 82 dates in 2013–2016. The sample bars
passed. Gross averaged +2.77% overall, below the +3% bar. Net at
doubled slippage was negative overall and in 2013–2016. The
later block averaged +3.32% gross, +1.14% at 1× and −0.96% at 2×.
The planned portfolio and validation stages were skipped.

| Development study to the close | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | +0.60% | −1.49% |
| 95% day-clustered interval | −0.56% to +1.68% | −2.65% to −0.40% |
| Summed event P&L | +$2,602 | −$6,452 |
| Daily event P&L t-statistic | 1.02 | −2.56 |
| Worst drawdown of summed events | −$1,225 | −$6,758 |

The day-clustered gross interval was +1.60% to +3.85%. The
dollar series sums independent hypothetical orders over all
3,352 development sessions. The simulated target shares
would exceed 5% of entry-bar volume for about 6% of events.

Run `20261116T220154Z_gpt_first_session_followthrough_df16ec8f`
used clean commit `d1ca6b3`, data build `447e58e098` and the
2003-09-10 through 2016-12-30 development period. Registration
`94e879a` preceded the run. All entries followed the signal by
one clock minute and all 202 session replays passed. This
adds one `new_listing_drift` trial. Validation and the sealed
holdout stayed closed.

## Execution and data limits

New securities have no trailing turnover at their first observed
session. The study used the cost model's 100-basis-point
half-spread fallback and estimated both sides from entry-bar
inputs. The saved mean base cost was 2.17%, of which 2.09%
was slippage. The portfolio would price an actual auction
exit separately. Even before costs, the frozen study missed
the overall gross bar.

The standard quote planner produced 70 pre-seal development
windows for this run. The files can measure the entry ask,
quote depth and spread against the fallback. The current planner
stops shortly after entry, so it cannot evaluate the closing
auction. The owner can download the sample using the existing
quote workflow. These measurements would inform calibration
for future first-session studies. They would leave this run's
prespecified decision intact.
[Kinn quote workflow](../../docs/decisions/0012-quote-sample.md)

The study report displays missing median trailing turnover as
`$nan`. Its liquidity rows omit all of these events because
there is no unknown-liquidity row. The quote planner assigns
missing turnover to its lowest bucket. For this cohort the
owner should interpret that label as unknown. The selected
companies are first matched by Kinn. Their actual listing
date, previous trading history and live execution are unverified.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 0 | — | — | $0 | $0 |
| 2004 | 19 | +1.43% | −0.68% | +$539 | −$260 |
| 2005 | 17 | −0.50% | −2.61% | −$166 | −$880 |
| 2006 | 19 | −0.18% | −2.25% | −$67 | −$848 |
| 2007 | 21 | +0.46% | −1.63% | +$193 | −$681 |
| 2008 | 5 | +4.75% | +2.70% | +$474 | +$270 |
| 2009 | 4 | −4.14% | −6.21% | −$330 | −$496 |
| 2010 | 13 | −0.27% | −2.35% | −$70 | −$610 |
| 2011 | 12 | −2.78% | −4.82% | −$662 | −$1,150 |
| 2012 | 17 | +1.84% | −0.22% | +$625 | −$74 |
| 2013 | 24 | +0.44% | −1.64% | +$212 | −$781 |
| 2014 | 35 | +0.70% | −1.41% | +$487 | −$978 |
| 2015 | 22 | +3.17% | +1.08% | +$1,393 | +$475 |
| 2016 | 10 | −0.11% | −2.20% | −$26 | −$441 |
