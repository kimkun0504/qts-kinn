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

## Addendum, 2026-11-16: at most two simultaneous positions

The fixed one-hour portfolio run `20261116T062349Z_gpt_relative_dislocation_reversal_034697eb`
passed the return and sample bars, and missed on stressed Sharpe. Its stored entry and
exit minutes show nine sessions with more than two overlapping trades. The absolute
number of overlaps is small, but related stocks can be hit by the same temporary
liquidity shock. Capping simultaneous exposure could reduce that concentration.
It could also discard valuable fills or increase dependence on admission order.

Test exactly one change, `risk.max_positions: 2`, in the liquid cohort's one-hour
configuration. The $2,000 target per order means the nominal concurrent target is
$4,000 on the $20,000 account. Preserve Kinn's reservation, expiry, buying power
and chronological priority rules. Leave all signal, universe, holding time and
cost settings as registered. The saved one-hour study and previous portfolio run
remain in the research record.

Run `development_liquid_one_hour_two_positions` once on 2003-09-10 to 2016-12-30.
Apply every original development portfolio gate, including the gross-return study
gate already assessed on the identical signal, 2013–2016 returns, and 2× daily Sharpe
strictly above 1. Compare the actual fills, total net and portfolio risk to the saved
uncapped-in-practice ten-slot variant. Count the trial in `intraday_rebound`.

Only if qualified, run `validation_liquid_one_hour_two_positions` once on 2017-01-03
through 2023-11-08. Apply the unchanged validation gates, including the +3% all-trade
mean at 1× overall and in the recent block and the stressed risk gates. Report the
average winner, average loser and sample size separately. No other position cap is
registered and the sealed holdout stays excluded.

## Addendum, 2026-11-16: relative recovery confirmation

The liquid one-hour signal requires a stock-specific 15-minute decline but accepts
an absolute one-minute recovery. A broad-market rebound can therefore qualify the
confirmation even if demand in the stock has yet to recover relative to its peers.
Test whether the recovery itself must exceed the synchronous market move. The
extra condition may delay entry or exclude some profitable common-market rebounds.

Use the fixed liquid cohort and one-hour exit with the original ten-slot capacity.
Keep the existing price drop, turnover and absolute 1% recovery conditions. In
addition, require the candidate's exact one-minute close-to-close return to exceed
the median exact one-minute return of the same large-cap anchors by at least
**one percentage point**. At least 30 anchors must print at both one-minute
endpoints. This uses completed bars only. Keep the original one-per-symbol rule
and take the first bar to meet every condition. All other parameters are identical
to the stored liquid one-hour portfolio, including the per-order target.

This is one fixed signal variant. Run `development_liquid_peer_recovery --study`
on 2003-09-10 through 2016-12-30 and apply the original development study gates
at the one-hour horizon. Recheck next-bar-only events if any study entries are
late. If qualified, record the develop decision before running
`development_liquid_peer_recovery` as a portfolio on the same dates. Apply the
original portfolio development gates, including the 2013–2016 returns and the
2× Sharpe gate. Compare actual risk and trade counts to the saved one-hour run
`20261116T062349Z_gpt_relative_dislocation_reversal_034697eb`.

If qualified, run `validation_liquid_peer_recovery` once on 2017-01-03 through
2023-11-08 under the existing, unchanged validation bars. These include mean net
of at least +3% at 1× across all completed trades overall and in the 2022+ block,
with the respective count and stress requirements. Count each run in
`intraday_rebound`. Later market data stays sealed.

## Addendum, 2026-11-16: a quiet baseline before the dislocation

Test a sudden break from a stable price against the existing broad dislocation rule.
A stock already moving widely before the measured decline can be actively repricing.
A sharp move from a narrow preceding range may instead reflect a temporary change
in demand for liquidity. Stability of the earlier bars can also omit volatile
stocks that offer genuine positive expectancy.

Start from the liquid one-hour portfolio with ten slots and the absolute recovery
condition. For a candidate at clock minute `t`, examine regular-session closes
labelled `t−25` through `t−15`, inclusive. Require the entire interval to be in
the regular session, at least nine observed closes, and a maximum close no higher
than 1.03 times the minimum. The 3% band is one quarter of the existing 12-point
dislocation threshold. The interval ends at the opening endpoint of the 15-minute
return and excludes the dislocation's interior. Missing prices stay missing.
Use the first bar satisfying the existing and new conditions. Keep execution,
exit, risk and every other signal input from the base `liquid_one_hour` rules.

One trial definition. Use `development_liquid_quiet_baseline --study` from
2003-09-10 through 2016-12-30, evaluating `r_60` with the existing full and recent
development study gates. Recheck on next-clock-minute fills if there are late
entries. Only if qualified, record the develop verdict and run the corresponding
`development_liquid_quiet_baseline` portfolio. Apply the existing development
return, sample and risk gates including stressed Sharpe above 1.

If qualified, run `validation_liquid_quiet_baseline` once from 2017-01-03 through
2023-11-08 under the original validation gates. In particular, require +3% net
per completed trade at 1× overall and in the 2022+ block. Keep the original
sample minima and the 2× stress requirements. The holdout remains excluded.
Count each run in `intraday_rebound` and report study or portfolio outcomes at
both costs, with yearly results, daily t-statistics and drawdown.
