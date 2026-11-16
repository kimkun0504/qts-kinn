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

## Addendum, 2026-11-16: selection by absolute liquidity

The original full-period study was positive and its later development block lost.
An exploratory development-only look at saved run
`20261116T061343Z_gpt_relative_dislocation_reversal_cbe31371` found that 39 of the
2013–2016 events had at least $10 million in prior median daily turnover. Their
mean was +3.14% gross and +2.08% at 2×. This is a small, selected subgroup.
Its results motivated a new hypothesis and cannot validate it.

Replace the tradable-stock selection by positive prior capitalisation **below
$10 billion** and at least **$10 million** in prior daily median turnover. The
$10 million breakpoint is the cost model's spread tier. The cap cutoff is the
lower bound of the existing anchor basket. This lets liquid mid-caps participate.
Remove the turnover-to-cap ratio. Keep the same $2 prior close floor, age floor,
reference stocks, return cutoffs, bar-turnover confirmation, next-minute entry,
auction exit, and account. Report actual bar-based capacity and encumbered capital.

Run one new variant with `development_liquid --study` on 2003-09-10 through
2016-12-30. Apply the exact original event-study gates, including the later
development block and expiry sensitivity. If they pass, commit that decision
and run `development_liquid` with the portfolio engine. Apply the unchanged
portfolio development gates. Only if they pass, run `validation_liquid` once
on 2017-01-03 through 2023-11-08. Apply the unchanged +3.00% and recent-regime
validation bars. Count each run in `intraday_rebound` and disclose that the
selector was motivated by development results. No other liquidity or cap
cutoff is registered. The holdout stays sealed.

## Addendum, 2026-11-16: exit after one hour

The liquid cohort was positive through the close, but the recent development gross
bar failed. Its published study report includes a one-hour outcome for each year.
A short-lived liquidity discount may be largely corrected within an hour, after
which a holder carries the longer-lived information component. This is an
exploratory choice made after reading development horizon results. It uses the same
data and does not constitute an additional independent signal test.

Freeze one exit: hold for exactly 60 clock minutes from the first entry fill,
then send a market sell at the first available bar. Preserve the closing auction
fallback and same-day exit. Kinn may fill in parts and a missing bar may delay
the sell. Use the same liquid cohort, signal, one-bar market entry, costs, account
and participation constraints. The event-study measure is the close after 60
one-minute bars, capped at the official close. The portfolio uses the next open
after the held interval and exit-side costs.

Use the saved `r_60` event return from
`20261116T062029Z_gpt_relative_dislocation_reversal_56620f46` to apply the original
development study gates at this horizon. The limit on recent years and the expiry
sensitivity remain the same. If they pass, commit the decision and run
`development_liquid_one_hour` in the portfolio engine, 2003-09-10 through
2016-12-30. No new event study repeats the same input and horizon. Apply the
original portfolio development gates. Only if all pass, run
`validation_liquid_one_hour` once, 2017-01-03 through 2023-11-08, under the original
validation gates, including the separate +3% recent return hurdle.

Count the portfolio runs as `intraday_rebound` trials and disclose the horizon
look. No other holding time is registered. Do not use sealed market data.
