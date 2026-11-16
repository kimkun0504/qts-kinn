# First-session follow-through

Registered 2026-11-16. When a stock begins trading, there is no prior market
close to anchor buyers and sellers. High turnover and a sustained rise during
the initial price discovery may reflect demand that lasts through the first
session. The opposing explanation is early scarcity or speculative demand
that fades after more holders can trade. This rule uses the first matched
session as a proxy. It can include relistings and delayed vendor matches.

The previous `new_listing_drift` trial used one through nine prior matched
sessions and required a rise from a near-flat 09:30 open. This variant
targets zero prior matched sessions and uses the first observed regular bar
as its clock. Charge both ideas to `new_listing_drift`. One definition is
registered, with no threshold sweep.

## Frozen definition

- Use Kinn's domestic common-stock membership with exactly zero
  prior matched sessions. There is no prior price or turnover filter.
  Starting from the second calendar year of the data (2004-01-02)
  avoids the startup cohort of names first observed when the dataset
  began. Gaps in coverage can still make an established company appear
  new. The data includes no verified IPO date in the strategy interface.
- Require the first observed regular-session bar to be labelled between
  09:30 and 12:30 ET inclusive, with a finite opening price at least
  $5. Discard premarket activity for this signal. Use the 30 clock
  minutes beginning with that first bar. Require at least 25 observed
  positive finite closes including actual closes on minutes 29 and 30
  of the interval, both at least 5% above the first regular bar's
  opening price. Use only completed bars. Require at least $2 million
  summed turnover through that decision bar, approximated by close
  times volume, and at least $40,000 of decision-bar turnover.
- Buy at market in the next clock minute only and exit in the same
  session's official closing auction, with the existing forced-exit
  fallback. Require the decision to fall at least 60 clock minutes
  before the calendar close. Use $20,000 equity and buying power,
  $2,000 target per position, ten reservations, 5% bar participation,
  and `ibkr_pro_tiered`. Use the cost model's unknown-liquidity spread
  when no prior turnover is available.

## Sequence and gates

1. Run `development --study` from 2003-09-10 through 2016-12-30.
   Use `r_close` for selection. Require 150 events on 90 dates and
   40 events in 2013–2016. Require gross mean at least +3% and
   positive mean at 2× overall and in 2013–2016, with a strictly
   positive full-period lower 95% day-clustered gross bound.
   If any entries happen after expiry, require the same gates on
   the next-clock-minute-only sample. Park after any miss.
2. After a committed develop verdict, run `development` once as a
   portfolio for the same dates. Require 150 trades on 90 dates
   and 40 trades in 2013–2016, mean net at least +2.5% at 1× and
   above +1% at 2× in both development blocks, 2× daily Sharpe
   strictly above 1 and worst 2× end-of-day drawdown below $10,000.
3. If qualified, run `validation` once on 2017-01-03 through
   2023-11-08. Require +3% mean net per completed trade at 1×
   and +1% at 2× overall and separately in 2022 through
   2023-11-08. Require 150 trades on 90 overall dates and 50
   trades on 30 recent dates, positive 1× mean in 2017–2021,
   stressed daily Sharpe above 1 and worst stressed end-of-day
   drawdown below $10,000.

Report counts, years, t-statistics, drawdowns and both cost cases.
Report conditional winners and losers separately for portfolio
stages. The study estimates both sides from the entry bar and
portfolio fills model opening prints, size and auction proceeds.
Current-vintage classifications, ticker matching and missing bars
affect the observed-age proxy. The holdout stays sealed.

## Addendum, 2026-11-16: decide after sufficient turnover

The fixed 30-minute study (`20261116T220154Z_gpt_first_session_followthrough_df16ec8f`)
cleared the sample requirements but averaged less than +3% gross and lost at
doubled slippage. The first 30 minutes can capture different amounts of price
discovery across stocks. A stock that is already trading heavily may show
evidence of sustained demand earlier. Buying earlier may also pay a wider
spread or buy the opening enthusiasm before the first pullback. The prior
study motivated this change. This is one additional timing look.

Keep the starting date, first observed session cohort, opening-price
floor, latest first bar, next-minute entry, closing auction, minimum
remaining session, risk and costs from the fixed rule. Keep the two
consecutive actual closes at least 5% above the first opening price,
$2 million cumulative regular-session turnover from the first bar,
and $40,000 of decision-bar turnover. Look for the first qualifying
completed bar on or before the 30th clock minute after the first
bar, counting the opening minute as minute one. Require at least
five valid observed closes through the decision and at least five
sixths of elapsed clock minutes observed. The latter reproduces
the 25-of-30 coverage at the original endpoint. The volume
threshold is measured only through each candidate bar.

Run `development_turnover_timing --study` on 2003-09-10 through
2016-12-30 and apply the original `r_close` study gates, including
the next-minute sensitivity if needed. Compare signal coverage,
timing and event returns with the fixed-clock run as a descriptive
diagnostic. After a committed develop verdict, run the
`development_turnover_timing` portfolio and apply the same
development gates. Only if qualified, run
`validation_turnover_timing` once on 2017-01-03 through 2023-11-08
under the unchanged +3% base-cost, sample and doubled-slippage
requirements, including the separate 2022–2023-11-08 block.

There is one varied timing rule. Use the existing unknown-liquidity
spread assumption. Count the runs in `new_listing_drift`. The sealed
holdout remains excluded.
