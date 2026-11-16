# Resumption momentum

Registered on 2026-11-16. A sharp upward move can interrupt continuous trading.
If buyers still pay above the earlier close after trading resumes, the interruption
may have deferred part of the buying. The opposing explanation is that the reopening
absorbed the imbalance and leaves a crowded long. This tests continuation after an
upward impulse. The earlier liquidity-gap reversal looked for a down-priced first
bar after a longer interruption. Count that related look in the broader research
program, and use family `resumption_momentum` for this direction and event.

Limit Up–Limit Down implementation was completed in May 2014. The candidate uses
only signals from May 12, 2014 onward, when the SEC's Phase II sample begins.
Absent minute bars do not identify an actual regulatory pause.
[SEC staff study on Limit Up–Limit Down](https://www.sec.gov/files/dera-luld-white-paper.pdf)

## Frozen definition

- Listed domestic common stock with at least 20 prior matched sessions, prior
  split-adjusted close of at least $2, prior daily median turnover of at least
  $1 million and prior market cap greater than zero and below $2 billion. Compute
  those selections from the pre-open panel.
- Within the regular session, look for **4–6 completely absent clock minutes**.
  Prior to the gap require the last five printed minute bars to be consecutive
  and the last close to be at least 8% above the first close. The range of missing
  bars allows for a pause beginning or ending partway through a clock minute.
- Require a printed resumption bar and an immediately following confirmation
  bar. Confirmation must close at least 1% above the resumption close, at or above
  the last pre-gap close, and trade at least $40,000 by close times volume. Take
  the first such confirmation per symbol between 09:45 and 14:45 ET, with at
  least 75 minutes left in that exchange session.
- Buy at market on the next clock minute only. Hold for 60 clock minutes from
  the first fill, then sell at market using the normal auction fallback. Same-day
  only. Use $20,000 equity and buying power, at most ten reservations, $2,000
  target size, 5% participation and `ibkr_pro_tiered`.

## Selection and validation

One definition. Count each run. The development configs span 2003-09-10 to
2016-12-30 to preserve the research split. Signals and applicable-session risk
measurements begin May 12, 2014.

1. Run `development --study`; use the saved `r_60` horizon, measured from the
   first market entry bar. Require at least 150 events on 90 dates and at least
   40 events in both 2014–2015 and 2016. Require gross mean at least +3% overall
   with a positive session-clustered lower 95% bound, and positive net at 2×
   in both blocks. If the study enters past expiry, apply the same gates to
   next-bar-only events as well. Any failure parks the strategy.
2. After a committed develop verdict, run `development` as a portfolio backtest.
   Apply the same sample bars, +2.5% overall mean net at 1×, above +1% overall
   at 2×, positive 2× net P&L in both blocks, end-of-day drawdown below $10,000
   at 2×, and 2× annualised daily Sharpe above 1 on applicable sessions.
   Report the standard full-calendar risk metrics as well.
3. Only if qualified, run `validation` once, 2017-01-03 through 2023-11-08.
   Require +3% mean net over all closed trades at 1× and +1% at 2× both overall
   and in 2022 through 2023-11-08, with 150 trades on 90 dates overall and 50
   trades on 30 dates in the recent block. Require positive 1× mean in 2017–2021,
   validation 2× Sharpe above 1 and end-of-day drawdown below $10,000 at 2×.

Report annual results, daily t-statistics and drawdown at both costs. Report
mean winners separately. The trade-break proxy can reflect sparse trades or
missing data. The entry and exit require separate quote and tick validation
before a paper-trading claim. Exclude the sealed holdout from all phases.
