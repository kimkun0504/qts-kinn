# Gap washout reclaim

Registered 2026-11-16. Stocks that open sharply above the prior close can have
persistent selling from holders who entered before the open. Require a visible
selloff and then a recovery above the volume-weighted price of regular-session
trades. If the initial gap reflected genuine new demand and the early selling
has abated, a stock that retakes its volume-weighted price may continue to
recover. A VWAP crossing can also be a brief bounce before more selling.

Earlier studies bought positive gaps that were already extending or measured
VWAP position at a fixed time. This rule observes an ordered path after the
open. It trades a recovery from a down leg and counts in `intraday_rebound`.
Treat the prior gap, volume and reversal studies as related searches. The
mechanism is an inference from prints. Kinn observes neither trader identity
nor signed order flow.

## Frozen definition

- Pre-open universe is listed domestic common stock, including names that later
  delist, with at least 20 matched prior sessions, prior split-adjusted close of
  at least $2, prior 20-session median dollar turnover of at least $1 million,
  and positive prior market cap below $2 billion.
- Require an observed regular-session opening minute labelled 09:30 ET whose
  open is at least 20% above the split-adjusted prior close. Compute running
  regular-session VWAP from observed minute closes and share volumes. Use the
  volume times close proxy for within-minute traded value. Exclude premarket.
- At decision minute `t` require the minimum observed regular-session close
  through `t-2` to be at least 10% below the opening price. Require actual
  bars at `t-2`, `t-1` and `t`. The close at `t-2` must be below its own
  running VWAP. The closes at `t-1` and `t` must be above their corresponding
  running VWAPs, and the close at `t` must exceed that at `t-1`. Require at
  least $40,000 in turnover in the decision bar, the $2,000 target divided
  by 5% participation. Take the first qualifying completed bar per symbol,
  labelled 10:00 to 14:45 ET inclusive and at least 75 minutes before the
  calendar close.
- Buy at market on the next clock minute only, expiring at the end of that
  minute. Exit at market after 60 clock minutes from first fill, using the
  existing auction fallback. Use $20,000 equity and buying power, $2,000 per
  order, ten concurrent reservations, 5% bar participation and
  `ibkr_pro_tiered`. Positions open and close on the same day.

The gap threshold selects a pronounced overnight move and the washout threshold
is half that threshold. The rule freezes one variant. There is no time or price
threshold sweep.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30. Judge the
   `r_60` horizon only. Require at least 150 measured events over at least 90
   sessions and at least 40 events in 2013–2016. Require mean gross of at least
   +3% both overall and in 2013–2016, positive mean net at 2× in both blocks,
   and a strictly positive day-clustered lower 95% gross bound overall. If the
   study enters past expiry, require every gate on the next-minute-only set
   as well as the full set. Park after any miss.
2. After a committed develop verdict, run `development` as a portfolio on the
   same dates. Require at least 150 fills on at least 90 sessions and 40 fills
   in 2013–2016. Require net per trade of at least +2.5% at 1× and above +1%
   at 2× both overall and in 2013–2016, daily annualised Sharpe strictly above
   1 at 2× and worst end-of-day drawdown below $10,000 at 2×. Park after any miss.
3. If qualified, run `validation` once on 2017-01-03 through 2023-11-08. Require
   +3.00% mean net across all completed trades at 1× and +1.00% at 2×, both
   overall and in 2022 through 2023-11-08. Require at least 150 trades on 90
   dates overall, 50 trades on 30 dates in the recent block, positive 1× mean
   per trade in 2017–2021, a full-period 2× daily Sharpe above 1 and a worst
   2× end-of-day drawdown under $10,000. Report winners and losers separately.
   The sealed holdout is excluded.

Count each run. Report yearly results, daily P&L t-statistics and drawdown at
1× and 2×. Study dollars sum independent hypothetical positions. Next-minute
opens and bar participation approximate real fills. Quotes, execution through a
halt, corporate actions and the latest-vintage company classification remain
limitations.
