# Market recovery lag

**Verdict: park.** The one-hour study produced 18 events on six
dates and zero in 2013–2016. It averaged +0.39% gross, −0.20%
net at base costs and −0.62% at doubled slippage. The sample
and return bars failed. The 95% day-clustered gross interval
was −2.05% to +3.28%, missing the positive lower bound. Portfolio
development and validation were skipped.

| One-hour development study | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | −0.20% | −0.62% |
| 95% day-clustered interval | −2.55% to +2.53% | −2.88% to +1.99% |
| Summed event P&L | −$72 | −$222 |
| Daily event P&L t-statistic | −0.15 | −0.45 |
| Worst drawdown of summed events | −$435 | −$520 |

The stored close horizon averaged +3.55% and +3.13% respectively
at 1× and 2×, on the same clustered sample. The prespecified
decision used one hour. The six dates and the absence of events
in later development limit the evidence at either horizon.

Dollar metrics sum independent hypothetical orders over all
3,352 development sessions. About 28% of the event notionals
would have required more than 5% of their entry bar's shares.
Both marketable legs are costed from the entry bar. Minute
opens and quoted depth remain unverified.

Run `20261116T215351Z_gpt_market_recovery_lag_8b4893a6` used
clean commit `4d4084a9`, build `447e58e098`, and 2003-09-10
through 2016-12-30. Registration `dac04fc` preceded the run.
All 18 study entries followed the signal by one clock minute,
and all six signal-session replay checks passed. This adds
one `intraday_rebound` trial. Validation and the sealed holdout
stayed closed.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003–2007, each year | 0 | — | — | $0 | $0 |
| 2008 | 13 | +1.04% | +0.57% | +$271 | +$150 |
| 2009–2010, each year | 0 | — | — | $0 | $0 |
| 2011 | 5 | −3.44% | −3.73% | −$343 | −$372 |
| 2012–2016, each year | 0 | — | — | $0 | $0 |
