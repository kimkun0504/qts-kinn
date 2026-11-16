# Gap washout reclaim

**Verdict: park.** The one-hour development study averaged −0.53% gross,
−1.07% net at base costs and −1.40% net at doubled slippage. It measured
130 events on 109 dates, below the 150-event minimum. The 42 events on 40
dates in 2013–2016 averaged −0.31% gross, −0.82% net at base costs and −1.16%
net at doubled slippage. The return gates and the positive lower confidence
bound failed. The portfolio and validation phases were skipped under the
preregistered rules.

Run `20261116T211807Z_gpt_gap_washout_reclaim_c2c9fd2e` used clean commit
`3afe999b` and build `447e58e098`. Registration `04f5606` preceded the run.
The development window was 2003-09-10 through 2016-12-30. This adds one
counted `intraday_rebound` trial. Each of the 130 simulated entries followed
the signal by one clock minute. All 109 signal-session lookahead checks
passed. Validation and the sealed holdout stayed closed.

| One-hour development study | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | −1.07% | −1.40% |
| 95% day-clustered interval | −1.69% to −0.41% | −2.02% to −0.73% |
| Summed event P&L | −$2,773 | −$3,633 |
| Daily event P&L t-statistic | −2.89 | −3.58 |
| Worst drawdown of summed events | −$2,903 | −$3,726 |

The 95% session-clustered gross interval was −1.15% to +0.13%. Dollar metrics
sum the saved independent hypothetical events across the 3,352 development
sessions. The study estimates both marketable legs with the entry bar's cost
inputs and does not cap study event shares. About 12% of event orders would
exceed the configured 5% of entry-bar volume.

The washout and subsequent VWAP reclaim gave no evidence of further buying
at the registered horizon. The loss before costs means cheaper execution
alone cannot meet the return hurdle on this sample. A genuinely different
signal, such as one measuring a known catalyst or signed order flow, would
need its own registration and point-in-time inputs.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | −5.18% | −5.41% | −$103 | −$108 |
| 2004 | 7 | −1.70% | −1.93% | −$237 | −$270 |
| 2005 | 1 | +0.68% | +0.41% | +$13 | +$8 |
| 2006 | 0 | — | — | $0 | $0 |
| 2007 | 12 | −0.03% | −0.36% | −$7 | −$87 |
| 2008 | 38 | −1.10% | −1.41% | −$833 | −$1,072 |
| 2009 | 14 | −2.61% | −3.02% | −$730 | −$843 |
| 2010 | 3 | −0.82% | −1.22% | −$49 | −$73 |
| 2011 | 6 | −0.20% | −0.58% | −$24 | −$70 |
| 2012 | 6 | −0.94% | −1.22% | −$112 | −$145 |
| 2013 | 4 | −4.13% | −4.59% | −$330 | −$366 |
| 2014 | 13 | −0.65% | −0.93% | −$169 | −$241 |
| 2015 | 10 | +0.07% | −0.26% | +$14 | −$53 |
| 2016 | 15 | −0.69% | −1.05% | −$207 | −$314 |
