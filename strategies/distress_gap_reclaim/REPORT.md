# Distress gap reclaim

**Verdict: park.** The one-hour study averaged −0.02% gross,
−0.50% net at base costs and −0.80% at doubled slippage. It
measured 102 events on 64 dates, including only seven events on
seven dates in 2013–2016. In that later block the gross mean was
+1.39%, with net of +0.86% at 1× and +0.51% at 2×. The study
failed the full and later sample and gross-return gates. The
full-sample lower confidence bound was negative. Portfolio
development and validation were skipped.

| One-hour development study | 1× slippage | 2× slippage |
|---|---:|---:|
| Net per event | −0.50% | −0.80% |
| 95% day-clustered interval | −2.40% to +1.11% | −2.71% to +0.83% |
| Summed event P&L | −$1,014 | −$1,634 |
| Daily event P&L t-statistic | −0.56 | −0.90 |
| Worst drawdown of summed events | −$1,430 | −$1,891 |

The 95% day-clustered gross interval was −1.92% to +1.59%.
Results concentrated in 2008, with 76 of 102 events. The
stored close horizon averaged +1.42% net at 1× and +1.12% at
2×. That horizon is descriptive, and the registered decision
uses one hour. The daily dollar series sums hypothetical orders
over all 3,352 development sessions. About 8% of order sizes
would exceed the 5% entry-bar participation limit. The study
costs both legs from entry-bar inputs and leaves actual quoted
size and fills unverified.

Run `20261116T215738Z_gpt_distress_gap_reclaim_71532b1a` used
clean commit `c73d77f8`, data build `447e58e098` and the window
2003-09-10 through 2016-12-30. Registration `bf0573f` preceded
the run. All entries followed their signal by one clock minute
and all 64 replay checks passed. This adds one
`opening_gap_continuation` trial. Validation and the sealed
holdout stayed closed.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 0 | — | — | $0 | $0 |
| 2004 | 0 | — | — | $0 | $0 |
| 2005 | 2 | −1.58% | −1.83% | −$63 | −$73 |
| 2006 | 0 | — | — | $0 | $0 |
| 2007 | 9 | −1.64% | −1.91% | −$293 | −$341 |
| 2008 | 76 | −0.34% | −0.66% | −$522 | −$1,002 |
| 2009 | 7 | −1.28% | −1.48% | −$178 | −$207 |
| 2010 | 0 | — | — | $0 | $0 |
| 2011 | 1 | −3.90% | −4.14% | −$78 | −$83 |
| 2012 | 0 | — | — | $0 | $0 |
| 2013 | 0 | — | — | $0 | $0 |
| 2014 | 1 | +12.86% | +12.52% | +$257 | +$250 |
| 2015 | 1 | +6.13% | +5.76% | +$123 | +$115 |
| 2016 | 5 | −2.59% | −2.95% | −$259 | −$295 |
