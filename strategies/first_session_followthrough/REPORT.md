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

## Entry based on completed turnover

**Decision: park.** The earlier rule found 336 events on 296
dates. It averaged +2.86% gross to the close, +0.66% net at 1×
and −1.45% at 2×. It passed the sample bars and missed the
gross and stressed return bars. In 2013–2016, 147 events on 129
dates averaged +0.78% and −1.34% at 1× and 2×. The on-time
subset also missed the return bars. Portfolio development and
validation were skipped.

| Development study to the close | Full 1× | Full 2× | On-time 1× | On-time 2× |
|---|---:|---:|---:|---:|
| Mean net per event | +0.66% | −1.45% | +0.37% | −1.74% |
| Summed event P&L | +$4,393 | −$9,733 | +$2,471 | −$11,525 |
| Daily event P&L t-statistic | 1.13 | −2.50 | 0.70 | −3.23 |
| Worst drawdown of summed events | −$2,549 | −$10,105 | −$3,350 | −$11,897 |

The study advanced three entries beyond expiry. Those rows
are absent from the 333 on-time events across 294 dates.
On-time gross averaged +2.58% overall, with a 95%
day-clustered range from +1.58% to +3.68%. The 145 on-time
events in 2013–2016 averaged +2.46% gross, +0.25% net at 1×
and −1.88% at 2×. Daily statistics sum independent
hypothetical orders over all 3,352 development sessions.
Both legs use entry-bar estimated costs and the same
unknown-liquidity spread fallback.

The rule retained all 218 original stock-days and added 118.
It moved 215 retained signals earlier, by a median of 22
minutes. Among the 217 common cases with on-time entries in
both studies, the mean rose from −1.58% to +0.55% at 2×.
Restricting an early entry to this overlap would use the later
30-minute confirmation. The 116 on-time new stock-days
averaged −6.01% at 2×. The actual early rule trades both groups.

Run `20261116T220522Z_gpt_first_session_followthrough_56854497`
used clean commit `17ce6889`, build `447e58e098` and development
dates 2003-09-10 through 2016-12-30. Registration `e7135d6`
preceded the run. All 296 lookahead replays passed. This
adds one counted `new_listing_drift` trial. The validation
period and the sealed holdout stayed closed.

| Year | On-time events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 0 | — | — | $0 | $0 |
| 2004 | 34 | +2.09% | −0.05% | +$1,411 | −$36 |
| 2005 | 29 | −0.63% | −2.77% | −$354 | −$1,588 |
| 2006 | 25 | +0.19% | −1.86% | +$99 | −$921 |
| 2007 | 31 | +1.68% | −0.43% | +$1,032 | −$266 |
| 2008 | 9 | +1.81% | −0.33% | +$324 | −$59 |
| 2009 | 5 | +1.81% | −0.26% | +$181 | −$25 |
| 2010 | 15 | +1.67% | −0.42% | +$498 | −$126 |
| 2011 | 17 | −3.51% | −5.59% | −$1,188 | −$1,891 |
| 2012 | 23 | −0.50% | −2.59% | −$228 | −$1,182 |
| 2013 | 41 | +1.56% | −0.55% | +$1,279 | −$447 |
| 2014 | 54 | −1.82% | −3.94% | −$1,965 | −$4,247 |
| 2015 | 34 | +1.68% | −0.45% | +$1,133 | −$308 |
| 2016 | 16 | +0.78% | −1.35% | +$249 | −$431 |
