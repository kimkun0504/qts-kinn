# Trade-size expansion after an available earnings disclosure

**Verdict: park.** The frozen study produced only 2 completed
events on 2 dates. Their mean was +2.52% net at
base costs and +2.23% at doubled slippage. This is
far below the required sample, regardless of the positive
observed returns. It does not establish an alpha. No development
portfolio or validation run was made. No parameter was changed
to increase the sample after seeing it.

Run `20261118T152834Z_gpt_earnings_trade_size_shift_e247be80` used 2003-09-10 through
2016-12-30, data build `447e58e098`, clean
commit `3e3aa83e` and Form 8-K input
`2578b76aa1` (`form8k-1`).
Hypothesis commit `9160555` preceded implementation and every
empirical run. The owner authorized the existing transaction-
count view, recorded in OWNERS.md and the scoped request. No
data rebuild or download was needed. This is one new counted
trial in `big_prints`, bringing its charge to 50, including
49 declared prior looks. Related momentum studies remain part
of the broader search history.

## Development measurements

| Measurement | Base slippage | Doubled slippage |
|---|---:|---:|
| Completed events | 2 | 2 |
| Mean net/event | +2.52% | +2.23% |
| Sum of event P&L | $98.79 | $87.36 |
| Daily event P&L t-statistic | 1.41 | 1.41 |
| Observed event-series drawdown | $0.00 | $0.00 |
| Winning events | 2 | 2 |
| Mean winner | +2.52% | +2.23% |
| Losing events | 0 | 0 |
| Mean loser | N/A | N/A |

The gross mean was 2.9754%, below the
registered +3% bar. There were 2 completed events in
2013–2016, against the required 40, and 2 overall,
against 150 on 90 dates. Both events belong to the later
window, so its trade means equal the full sample. These sample
misses prevent advancement. There were no unfilled or unresolved
orders, late entries or exits at or after 16:00.

The runner's whole-day percentile bootstrap mechanically gives
a gross interval of +2.62% to
+3.33%, a base net interval of
+2.29% to +2.76%,
and a stressed interval of +2.02% to
+2.44%. With only two observed positive
days, this resampling cannot represent unseen adverse outcomes.
The positive bounds are not reliable evidence of an edge.
Likewise, zero observed drawdown is not a useful risk estimate
from this sample. The predefined sample bars are decisive.

Dollar diagnostics use stored filled shares times entry price,
apply the stored net event returns, and sum by date across all
3352 registered sessions. The mean filled notional was
$1,954.54 against the
$2,000 target. This is isolated event P&L; capital constraints
and account-portfolio drawdown were not measured. The mean
baseline round-trip cost was +0.45%,
including +0.16% fees and commissions and
+0.29% slippage.

## Annual development results

| Year | Completed events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2004 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2005 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2006 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2007 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2008 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2009 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2010 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2011 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2012 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2013 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2014 | 1 | +2.76% | +2.44% | $54.76 | $48.50 |
| 2015 | 0 | N/A | N/A | $0.00 | $0.00 |
| 2016 | 1 | +2.29% | +2.02% | $44.03 | $38.86 |

## Availability, execution and audit limits

The newly exposed transaction counts remain aligned with the
price bars and are truncated in prefix replay. Missing values
are preserved and cannot become inferred zero counts. The full
strategy replay passes; an intentionally future-count-dependent
strategy is caught by the same checker. The complete repository
suite, Ruff and import contracts pass. Replay checks passed on
both empirical signal sessions. Every entry was in its one
eligible next clock minute. The maximum elapsed holding period
was 121 minutes because timed liquidation can require retries.

The ratio of aggregate volume to count is not investor identity
or a verified distribution of price-setting trade sizes. Vendor
sale conditions may affect aggregate fields differently. The
earnings flag follows the next-session rule; it does not reveal
an earnings beat or contemporary news arrival. The market-cap
and security-category limitations of the panel remain.

Fills use `minute_open_proxy-1`. Completed execution-bar range
and volume affect cap acceptance, so passing signal replay does
not verify causal opening-fill selection. This remains an
unverified model assumption; any apparent quantitative pass
would need quote checks before a trading claim. See
`docs/requests/2026-11-18-opening-fill-selection-audit.md`.
The count-view change did not alter the cost model or fill policy.

An earlier public documentation search accidentally exposed
illustrative post-seal AAPL rows. The strategy and thresholds
were committed before that search, and the example was not used
to change them. The incident remains in
`docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`.
Zero post-seal exposure cannot be claimed. This empirical run
loaded no validation period, sealed folder or date on or after
2023-11-09, and no holdout backtest was run. All numerical
measurements above derive from this run's saved manifest,
`study.json`, part counts and `events.parquet`.
