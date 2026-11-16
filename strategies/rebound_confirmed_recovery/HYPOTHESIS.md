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
