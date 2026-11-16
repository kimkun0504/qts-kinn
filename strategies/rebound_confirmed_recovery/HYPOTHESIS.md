# Rebound after a confirmed recovery

Preregistered by GPT on 2026-11-15. A blind bid below the event close gives a good price
and takes the risk that the reason for the selling is still in force. This test gives up
time and pays for immediacy to buy only after a second completed close shows recovery.
The question is whether avoiding adverse selection is worth the extra execution cost
and leaving behind rebounds that recover too fast. The recovery must still be observable
at a price at or below the benchmark's passive bid.

Claude's `x_o4` is the fixed comparison. It posts a passive buy 4% below the trigger.
Its two stored runs and the subsequent tick check are listed below. The tick check
supports the baseline's entry fills at this size. It does not measure fills for the
new entry. Claude's current sweep varies bid depth and laddering. This variant uses the
same reference price and changes the decision to trade. The family is `intraday_rebound`.
There were 62 shared trials at the registry check before registration, including nine
pre-registry looks and runs still in progress.

| Reference | Run ID | 1× net/trade | 2× net/trade |
|---|---|---:|---:|
| `x_o4` development | `20261115T232205Z_claude_rebound_limit_84ff9c3d` | +1.34% | +1.24% |
| `x_o4` validation | `20261115T233007Z_claude_rebound_limit_eec4a69e` | +1.30% | +1.20% |
| Validation with the tick entry check | `20261116T012801Z_claude_rebound_limit_0e3f2a2d` | — | +1.17% |

## Frozen definition

1. Use the same pre-open universe as `x_o4`. Listed domestic common shares with prior
   close at least $1, prior 20-session median daily dollar volume at least $250,000 and
   at least 20 prior sessions. Include securities subsequently delisted. Exclude names
   with a prior-session-window 8-K, a regular-session opening price more than 5% below
   prior close, or pre-market dollar volume of at least 5% of prior daily median.
2. Use the first regular-session minute close at least 10% below the split-adjusted
   prior close. The bar's label must be between 09:35 and 15:00 ET inclusive. If the
   first cross comes earlier, ignore the symbol for the session. Let the reference be
   96% of the event close, rounded to cents if the event close was at least $1 and
   four decimals otherwise, as in `x_o4`.
3. Inspect the ten clock minutes after the event, within the regular session. At the
   first bar that closes at least 1% above the lowest close on an earlier bar in that
   window and still at or below the reference, signal a single market buy. The prior
   minimum must already exist. The window starts on the bar after the event. A low
   trade print alone cannot create the signal.
4. Enter on the next clock minute's bar. Expire at the end of that bar. Hold to the
   same session's official closing auction with the normal forced-exit fallback.
   Use the same $20,000 equity and buying power, $2,000 target positions, 5% entry-bar
   participation and `ibkr_pro_tiered` as the benchmark. Kinn sizes market orders at
   the signal close and can fill at a different price. Marketable fills and the closing
   auction remain modelled.

## Sequence and decision bars

One fixed variant. The only planned runs are the development event study, a development
portfolio backtest if the study qualifies, and one validation of the frozen variant if
the development backtest qualifies. Every run counts. No market data on or after
2023-11-09 may be used.

1. **Development study**, 2003-09-10 through 2016-12-30, `development --study`. Use
   `r_close` only. Develop with at least 200 events across at least 120 dates, mean
   gross at least +1.30%, a strictly positive day-clustered 95% lower bound on gross,
   and positive mean net at 2× both overall and in each half (2003–2009, 2010–2016).
   The study charges both sides using the entry bar. The full engine prices the
   closing auction separately, so the study gate screens for plausible upside.
   If the study uses later entries than the expiry, apply the same gate to the
   on-time subset of the saved rows. A failure parks the strategy.
2. **Development backtest**, same dates, `development`. Advance only if it beats the
   exact stored `x_o4` development means at 1× and 2×, with at least 200 trades
   across 120 dates, positive 2× P&L in both halves, daily Sharpe above 1 at 2×
   and worst end-of-day drawdown less than $10,000 at 2×. A failure parks the strategy.
3. **Validation**, 2017-01-03 through 2023-11-08, `validation`. Compare exact 1× and 2×
   mean net returns to the stored `x_o4` validation means, using the same build.
   Require at least 150 trades across 100 dates, 2× Sharpe above 1 and worst end-of-day
   drawdown less than $10,000 at 2×. Judge the +2.00% research target and the +3.00%
   stretch separately at 1×. Distinguish a higher 1× point estimate from stronger
   evidence by reporting a 95% paired session bootstrap interval for the difference
   in 1× mean net per trade, resampling identical calendar dates across both runs
   and taking the ratio of summed trade returns to summed counts within each strategy.
   Use 5,000 resamples with seed 0. The shared family has already seen this validation
   period. A point-estimate win here calls for a separate fill check before any
   paper-trading claim.

Report both costs, event or trade counts, daily dollar P&L t-statistics, drawdowns and
annual results. Event-study dollar statistics are unconstrained hypothetical P&L.
Minute opens and auctions do not establish executable quotes or order size. The
pre-open filing proxy misses announcements, stale closes and splits can distort drops,
and stored category labels have the known snapshot caveat.

## Addendum, 2026-11-15: volume and momentum at confirmation

The original portfolio run (`20261116T013621Z_gpt_rebound_confirmed_recovery_2b36bc0c`)
earned +1.69% per trade at 1× and +1.13% at 2×, with 0.42 annualised Sharpe at 2×.
Its average executed order was $1,376 against the $2,000 target. This fixed joint test
asks whether buying on a rising minute with more observed turnover preserves the rebound
while making the next fill less costly and less dependent on thin prints.

Use the original event, reference price, recovery window and eligibility. Within that
same window, take the first confirmation that also meets **both** criteria:

- The confirmation close is strictly higher than the close one clock minute earlier.
  Both must be post-event bars. A stale print does not count.
- Confirmation-bar turnover, approximated by close times volume, is at least **$40,000**.
  This is the $2,000 order divided by the 5% participation rate, fixed from account
  mechanics. It measures the completed signal bar. The simulator still sizes and caps
  the order using the actual next bar. Turnover measures two-sided activity and cannot
  establish buy-side imbalance, next-bar depth, or a fill at the signal price.

Use the same next-minute-only market order, auction exit, risk, and costs. The added
conditions can delay the confirmation or suppress it. This test measures their joint
effect together with that timing change. No separate threshold or factor sweeps are
registered. The existing development runs are comparators and will not be rerun.

The branch starts from Kinn's published integration tip `462efdb`. The shared
`intraday_rebound` count was 65 at registration, including prior looks. The original
confirmed entry is the control and `x_o4` is the fixed passive single-entry comparison.
The later passive ladder reports filled rungs as trades and is separate context.

1. Run `development_volume_momentum --study` on 2003-09-10 through 2016-12-30.
   Advance using the original study gate at the close: at least 200 events across
   120 sessions, gross mean at least +1.30%, positive lower 95% day-clustered
   gross interval, and positive 2× mean net overall and in each of 2003–2009 and
   2010–2016. Recheck the same gates on next-bar-only events if the study entered
   any after expiry. Compare entry-bar capacity and costs with the saved original
   study. Park if a gate fails.
2. After a committed develop verdict, run `development_volume_momentum` as a portfolio
   backtest on the same dates. Require at least 200 trades across 120 sessions, 1× mean
   net per trade at least equal to the original confirmed-entry portfolio, 2× mean
   net per trade higher than both fixed development comparators, positive 2× dollar
   P&L in both development halves, 2× annualised daily Sharpe above 1 and 2× worst
   end-of-day drawdown under $10,000. Use exact stored comparator values. Report mean
   executed notional, round-trip cost and the share of net profit from the strongest
   year as diagnostics. Park if a gate fails.
3. If qualified, run `validation_volume_momentum` once on 2017-01-03 through 2023-11-08,
   with the same comparison and risk bars as in the original validation plan. Retain
   the +2% target and +3% stretch at 1×. Use the preregistered paired-session bootstrap
   against `x_o4` for the difference in mean at 1×, and require an actual fill check
   before paper trading. The original confirmed entry has no validation result.

Count every run. Report both cost scenarios, counts, daily t-statistics, drawdowns
and yearly returns. Never query the sealed holdout.

## Addendum, 2026-11-16: bid at the observed low after confirmation

This is one execution variant of the registered volume-and-momentum signal. The stored
event study `20261116T020656Z_gpt_rebound_confirmed_recovery_eebfba4c` already passed the
signal's develop gate. A second identical event study cannot measure a limit because the
study uses a next-bar market entry. The market-entry portfolio version earned +1.75% at
1× and +1.28% at 2×, with daily Sharpe 0.45 at 2×. Lower costs on those same fills were
insufficient on their own. This test changes both the price and which orders fill.

The temporary imbalance may return to a level the market already tested after the first
recovery. A bid at the trough can buy at a lower price and avoid chasing that recovery.
A decline through the trough can instead reflect renewed informed selling. The benchmark
ladder uses fixed offsets and exposes capital before confirmation. The proposed order
uses the observed pre-confirmation minimum close and begins only after recovery.

- Keep the eligible stock, trigger, exact recovery bar, volume and momentum rules,
  target order, account, and closing-auction exit from the previous addendum.
- When the recovery is confirmed, post a buy limit at the lowest post-event close that
  preceded that confirmation. Round down to the nearest cent. Skip the order if the
  resulting limit is below $1. The running minimum is known at the signal bar close.
- Use one order per symbol, active from the next minute through confirmation + 5 clock
  minutes, inclusive, subject to Kinn's session entry cutoff. Use the normal one-tick
  through rule and 5% bar participation. Fill at the bid without price improvement.
  Confirming quotes and volume actually traded through the limit would need a separate
  execution audit. Keep `ibkr_pro_tiered` and the next-day-flat rule.

**Development:** `development_volume_momentum_retest` through the portfolio engine on
2003-09-10 through 2016-12-30. Count one new trial in `intraday_rebound`. Require 150
filled trades across 90 dates, at least 40 trades in 2013–2016, at least +2.5% mean net
at 1× and above +1% at 2× both overall and in 2013–2016, full-period daily Sharpe above
1 at 2× and 2× end-of-day drawdown below $10,000. The stock selection and signal are
already frozen. No other order depth, age, direction, or exit is registered.

**Validation:** if development qualifies, run `validation_volume_momentum_retest` once
on 2017-01-03 through 2023-11-08. Require +3.00% arithmetic mean net across all completed
trades at 1× and +1.00% or more at 2×, both overall and in 2022 through 2023-11-08.
Require at least 150 trades across 90 sessions overall and at least 50 trades across
30 dates in the recent block, positive 1× mean in 2017–2021, 2× full-period daily Sharpe
above 1 and 2× drawdown below $10,000. Report mean winners separately from expectancy.

Use the built data. The published data-6 notes describe `447e58e098` as adding
`ret60_prev` while preserving the earlier panel inputs. The retest does not use that
feature. Compare executions against the saved market version and qualified passive
benchmarks. Report both costs, trade counts, t-statistics, drawdown and annual outcomes.
The sealed holdout stays excluded.
