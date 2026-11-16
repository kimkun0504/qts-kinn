# Liquidity gap reversal

**Verdict: park.** The 2003–2016 development study found five events on five dates, all
in 2015 and 2016. The +6.05% mean after base costs is a description of those five events.
The gross 95% session-clustered interval crossed zero, and both the full and later
development samples fell far short of the counts fixed in the [hypothesis](HYPOTHESIS.md).
The portfolio backtest and validation were not run.

Run `20261116T060652Z_gpt_liquidity_gap_reversal_e70139fb` used clean commit
`eedeced1`, hypothesis commit `eb4d5dd` and sealed-safe data build `447e58e098`.
This adds one trial to the shared `intraday_rebound` family. All five entries were
in the intended next bar and all five run-time lookahead replays passed.

| Return to the close | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net return per event | +6.05% | +5.36% |
| 95% session-clustered interval | −2.19% to +13.95% | −2.43% to +13.01% |
| Summed event P&L | +$604 | +$535 |
| Daily event P&L t-statistic | 1.21 | 1.14 |
| Worst end-of-day drawdown of summed events | −$155 | −$159 |

The gross mean was +7.00% (95% interval −1.79% to +15.13%). The dollar series sums
whole-share event P&L from the saved run over its 3,352 sessions, with zero on days
without events. These are unconstrained hypothetical events. Market open and auction
fills remain approximations. Bootstrap intervals with this few independent dates
are unstable.

| Year with events | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2015 | 3 | −0.44% | −1.03% | −$26 | −$61 |
| 2016 | 2 | +15.79% | +14.94% | +$630 | +$596 |

A separate test using timestamped trading pauses and valid resumption quotes could
establish a wider, more reliably defined sample. This trial only measured gaps in
the minute bars and its five observations cannot distinguish a transient effect from luck.
