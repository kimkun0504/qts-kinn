# Turnover compression breakout

**Verdict: park.** The frozen definition produced one event, in 2008, across
3,352 development sessions. The count gates required 150 events across 90
dates and at least 40 events in 2013–2016. There were zero events in that
later block. A day-clustered interval requires more than one active date.
The portfolio and validation stages were skipped.

| One-hour event study | 1× slippage | 2× slippage |
|---|---:|---:|
| Hypothetical net return | +6.62% | +6.31% |
| Summed event P&L | +$132 | +$126 |
| Daily event P&L t-statistic | 1.00 | 1.00 |
| Worst drawdown of summed events | $0 | $0 |

The figures describe a single hypothetical trade. The daily t-statistic
and drawdown follow mechanically from one profitable event and 3,351
zero-P&L dates. Gross at the preregistered hour was +7.16%. The
joint turnover, range and confirmation requirements gave too little
coverage to assess the mechanism.

Run `20261116T213524Z_gpt_turnover_compression_breakout_877dca6e` used
clean commit `71ea4f6e` and data build `447e58e098`. Hypothesis commit
`98d06e1` preceded the run. This is one additional counted trial in
`intraday_volume_surge`. The entry timestamp was one clock minute
after the signal and the signal-session replay passed. Market prices
and quoted depth at the fill were modelled from bars. The period was
2003-09-10 through 2016-12-30. Validation and the sealed holdout
stayed closed.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003–2007, each year | 0 | — | — | $0 | $0 |
| 2008 | 1 | +6.62% | +6.31% | +$132 | +$126 |
| 2009–2016, each year | 0 | — | — | $0 | $0 |
