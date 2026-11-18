# Distributed premarket price discovery

**Verdict: park.** The one frozen variant averaged
-1.01% net per completed event at base extended-hours
costs and -1.68% at doubled slippage. Gross mean
was -0.18%. Both the required sample and
return gates failed. No development portfolio or validation
run was made, and the candidate was not tuned after this result.

Run `20261118T135731Z_gpt_premarket_price_discovery_6fc253b3` used 2003-09-10 through
2016-12-30, data build `447e58e098` and clean
commit `6adfb823`. The hypothesis was committed
at `57c701d` before implementation or any empirical run.
This is one charged trial in `intraday_momentum`, for a current
family charge of 175 including 174 conservatively declared
prior looks. The registration explains the related studies;
this is not an independent first look at momentum.

## Development results

137 signals on 136 signal sessions produced
84 completed events on 83 dates and 53 unfilled entries.
No position remained unresolved. Entry and liquidation used
the portfolio simulator's capped execution, participation and
expiry rules, with capital constraints excluded for the study.

| Measurement | Extended baseline 1× | Doubled extended slippage |
|---|---:|---:|
| Mean net/event | -1.01% | -1.68% |
| Day-clustered 95% net interval | -2.58% to +0.71% | -3.26% to +0.04% |
| Sum of event P&L | −$1,145 | −$2,192 |
| Daily event P&L t-statistic | -0.83 | -1.57 |
| Worst end-of-day event drawdown | −$1,915 | −$2,858 |
| Winning events | 29 | 27 |
| Mean winner | +6.97% | +6.85% |
| Losing events | 55 | 57 |
| Mean loser | -5.22% | -5.71% |

The positive mean among winners does not satisfy the target.
Success is judged across all completed events. The full gross
95% interval was -1.73% to
+1.51%, below the +3% mean bar and with
a negative lower bound. Mean baseline fees and commissions
were +0.17%; mean baseline slippage was
+0.67%, for a total mean round-trip
cost of +0.83%.

There were 26 events on 25 dates in 2013–2016,
with -0.34% net at baseline and
-1.09% at doubled slippage. The registration
required 150 events on 90 dates overall and 40 events in this
later window, +3% gross and positive stressed net in both
windows. It failed those count and mean requirements.

Daily dollar statistics multiply each stored net event return
by its actual simulated filled notional and sum by date,
including every registered development session. The mean filled
notional was $1,863.58
against the $2,000 target. These are isolated event diagnostics,
not account returns or measured portfolio drawdowns. Sizing
and capital conflicts would need the separate portfolio run,
which the failed gate prohibits.

## Annual development results

| Year | Completed events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | -8.70% | -9.88% | −$170 | −$193 |
| 2004 | 8 | -2.32% | -2.93% | −$365 | −$462 |
| 2005 | 10 | -4.19% | -4.70% | −$558 | −$653 |
| 2006 | 5 | -1.98% | -2.70% | −$186 | −$254 |
| 2007 | 12 | +0.64% | -0.06% | $149 | −$17 |
| 2008 | 0 | N/A | N/A | $0 | $0 |
| 2009 | 6 | -2.00% | -2.68% | −$234 | −$314 |
| 2010 | 6 | -2.38% | -2.96% | −$281 | −$350 |
| 2011 | 5 | -1.47% | -2.04% | −$144 | −$199 |
| 2012 | 5 | +5.75% | +5.22% | $577 | $528 |
| 2013 | 4 | -4.83% | -5.54% | −$378 | −$433 |
| 2014 | 9 | +0.55% | -0.19% | $147 | $26 |
| 2015 | 11 | +1.29% | +0.51% | $403 | $250 |
| 2016 | 2 | -4.29% | -5.08% | −$104 | −$121 |

## Execution and interpretation

Every entry occurred in the next clock minute. All completed
positions exited before 09:30: 0 reached the regular open.
The mean elapsed holding period was 30.58 minutes
and the maximum was 38 minutes because liquidation
can require retries. No position was silently settled with
an earlier official auction price. Replay checks passed on
all 136 signal sessions, including each signal boundary.

Both cost cases had to respect the same opening limit cap.
The baseline multiplies `ibkr_pro_tiered` marketable spread and
impact by two; the stress doubles that baseline. This is a
fallback estimate with no measured premarket quotes or depth.
The execution bar's total volume and range approximate capacity
and costs after signal formation. The last observed completed
close can be stale when setting a retrying sell limit. Actual
opening-print liquidity and queue position remain unverified.

The code's mathematics, liquidity rejection, isolated CLI load,
prefix replay and synthetic premarket fill tests pass, along
with the execution regression suite, repository rules, Ruff
and import contracts. All empirical numbers above derive from
this run's manifest, `study.json`, part counts and saved
`events.parquet`. No raw writes, downloads, rebuilds, dates
on or after 2023-11-09, or validation data were used.

This rule offers no evidence of profitable continuation at
these premarket entries. Price-path efficiency and dispersed
activity did not overcome reversal and transaction costs in
this frozen study. The result does not justify an opposite-side
trade, a new threshold, or a claim that all intraday trading
is impossible.
