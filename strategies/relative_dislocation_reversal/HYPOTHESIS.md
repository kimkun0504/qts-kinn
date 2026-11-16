# Relative dislocation reversal

Registered on 2026-11-16. A sharp price drop in a stock can include a common market
component and a stock-specific component. If the stock-specific component reflects
temporary demand for liquidity, prices may recover after the first visible reversal.
An information shock could produce the same prices and keep falling. This uses a
synchronous large-cap reference and a pre-open stock selector based on historic dollar
turnover relative to company capitalisation. The ratio measures trading intensity and
does not measure free float. Charge the strategy to `intraday_rebound`.

## Frozen definition

- Begin with the point-in-time domestic common-stock universe, prior close of at
  least $2, median daily dollar turnover of at least $1 million over the previous
  20 sessions, and at least 20 prior matched sessions. Use no same-day volume or
  market cap in the pre-open stock selection.
- A tradable stock has positive prior market cap below $2 billion and prior
  median daily dollar turnover of at least **1% of that market cap**. Include
  delisted names when eligible. For the market reference use the other universe
  members with prior cap of at least $10 billion and trailing daily turnover of
  at least $20 million.
- At each minute close, compute the median 15-minute return of the reference
  stocks with actual closes at both endpoints, from the regular session. A
  reference value needs at least 30 eligible names with both closes. For each
  tradable stock require a last 15-minute return at least **12 percentage points
  below** that median, a close at least 1% above its own immediately preceding
  clock-minute close, and at least $40,000 signal-bar turnover (close times volume).
  The 15-minute and one-minute stock endpoints must be observed. The $40,000
  floor comes from the $2,000 target divided by the 5% participation rate. It
  does not guarantee liquidity after the signal.
- Take the first such completed bar per symbol from 09:50 to 14:45 ET inclusive,
  inside the regular session. Buy at market on the next clock minute only.
  Exit in the same day's closing auction. Use `ibkr_pro_tiered`, $20,000 equity
  and buying power, $2,000 target size, at most ten concurrent positions or
  orders, and 5% entry-bar participation.

## Tests and decision rules

One fixed definition. Every run counts. Development is 2003-09-10 through 2016-12-30.
Validation is 2017-01-03 through 2023-11-08. The sealed holdout is excluded.

1. Start with `development --study`. At the close horizon require at least 150
   events across 90 dates and at least 40 events in 2013–2016. Require gross mean
   of at least +3% and positive net at 2× both overall and in 2013–2016, with a
   strictly positive lower 95% day-clustered gross bound overall. If the study
   enters after expiry, use both the full sample and the saved next-bar-only
   subset to judge the gates. Any failure parks the strategy.
2. After a committed develop verdict, run the `development` portfolio backtest.
   Require at least 150 trades across 90 dates and 40 trades in 2013–2016, mean net
   of at least +2.5% at 1× and above +1% at 2× both overall and in 2013–2016, full
   sample daily Sharpe above 1 at 2× and 2× drawdown no greater than $10,000.
3. If qualified, run `validation` once. Require at least +3.00% mean net per
   completed trade at 1× and +1.00% at 2×, overall and in 2022 through 2023-11-08.
   Require at least 150 trades on 90 dates overall and 50 trades on 30 dates in
   that recent block, positive 1× mean in 2017–2021, 2× Sharpe above 1 and worst
   2× end-of-day drawdown below $10,000. Use all wins and losses in the mean and
   report their frequencies and conditional means separately.

Report both cost cases, t-statistics, drawdowns and yearly results. Modelled fill
prices and auction proceeds need separate verification with quotes and trades.
The large-cap reference controls for a common move imperfectly. Same-clock missing
bars can make the median depend on which names are actively printing, and stale
market caps or current-vintage labels can misclassify the cohort.
