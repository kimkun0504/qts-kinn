# Volume surge pullback

**Verdict: park.** The one-hour event study averaged +0.29% gross,
−0.38% net at base costs and −0.85% at doubled slippage. It produced
146 events on 135 sessions, below the 150-event bar. In 2013–2016,
71 events on 65 dates averaged +0.23% gross, −0.43% at base costs and
−0.90% at doubled slippage. The return bars and the positive lower
confidence bound failed. Both portfolio stages were skipped.

| One-hour study | Full sample 1× | Full sample 2× | On-time 1× | On-time 2× |
|---|---:|---:|---:|---:|
| Events | 146 | 146 | 143 | 143 |
| Mean net per event | −0.38% | −0.85% | −0.37% | −0.84% |
| Summed event P&L | −$1,110 | −$2,481 | −$1,071 | −$2,415 |
| Daily event P&L t-statistic | −0.99 | −2.17 | −0.96 | −2.12 |
| Worst drawdown of summed events | −$1,544 | −$2,687 | −$1,522 | −$2,620 |

The full-sample 95% day-clustered gross interval was −0.42% to +1.06%.
The corresponding net intervals were −1.09% to +0.39% at 1× and
−1.56% to −0.07% at 2×. The study admitted three entries two minutes
after the signal, beyond strategy expiry. Restricting to the 143
on-time events across 133 dates left +0.30% gross with a 95%
day-clustered interval from −0.47% to +1.07%. The 70 on-time events in
2013–2016 averaged +0.24% gross and −0.89% net at 2×. The verdict was
the same on both samples.

The gross move over the hour was smaller than the modelled cost.
About 25% of full-sample orders at the hypothetical size would
exceed the configured 5% of entry-bar volume. These are independent
event exposures rather than capital-constrained fills. Dollar
statistics include zero-P&L dates over all 3,352 development sessions.
The previous surge study motivated the setup. This follow-up evaluates
the pullback path on the same development period.

Run `20261116T213905Z_gpt_volume_surge_pullback_07284754` used clean
commit `43116331`, build `447e58e098` and the 2003-09-10 through
2016-12-30 period. Hypothesis commit `11fd99a` preceded the run.
All 135 signal-session lookahead replays passed. The study adds one
counted `intraday_rebound` trial. Validation and the sealed holdout
stayed closed.

| Year | On-time events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 0 | — | — | $0 | $0 |
| 2004 | 7 | −1.87% | −2.38% | −$261 | −$333 |
| 2005 | 4 | +3.30% | +2.89% | +$263 | +$231 |
| 2006 | 2 | −3.02% | −3.29% | −$121 | −$131 |
| 2007 | 7 | −1.82% | −2.19% | −$253 | −$305 |
| 2008 | 23 | +0.46% | −0.11% | +$210 | −$52 |
| 2009 | 12 | −1.83% | −2.24% | −$438 | −$537 |
| 2010 | 7 | +1.78% | +1.35% | +$249 | +$189 |
| 2011 | 9 | −0.59% | −1.03% | −$106 | −$186 |
| 2012 | 2 | −0.35% | −1.00% | −$14 | −$40 |
| 2013 | 10 | −0.07% | −0.52% | −$13 | −$103 |
| 2014 | 9 | +0.68% | +0.16% | +$123 | +$29 |
| 2015 | 24 | −1.05% | −1.47% | −$503 | −$704 |
| 2016 | 27 | −0.37% | −0.87% | −$206 | −$473 |
