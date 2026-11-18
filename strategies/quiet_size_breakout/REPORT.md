# Larger prints at a narrow-range breakout

**Verdict: park.** The primary had 48 development events
on 47 dates, averaging −0.05% net at
base costs and −0.27% at doubled slippage.
Its gross mean was +0.33%, far below the +3%
bar. The sample, full-period stressed mean and lower gross
confidence-bound requirements also fail. No portfolio or
validation run was made and no parameter was changed.

The control had 1147 events on 895 dates,
averaging −0.46% and −0.69%
net. The larger-print condition improves this descriptive
comparison but does not create the required return. It cannot
be called a validated edge or evidence identifying a buyer.

## Runs and registered decision

- Primary: `20261118T155218Z_gpt_quiet_size_breakout_6dddd7e7`, `development`.
- Control: `20261118T155337Z_gpt_quiet_size_breakout_df5b6ded`, `development_control`.
- Both used 2003-09-10 through 2016-12-30, build
  `447e58e098`, clean commit `0919e85`.
  Hypothesis commit `d52f235` preceded code and every run.
- Two new trials in `big_prints`, now charged
  52, including 49 declared prior looks.
  Related price, volume and rebound searches remain broader
  research history; this is not an independent first look.
- Every saved primary event exactly matches a control event,
  including entry, returns and costs. The fixed decision time
  prevents favorable later-event selection.

## Full development at r_120

| Measurement | Primary 1× | Primary 2× | Control 1× | Control 2× |
|---|---:|---:|---:|---:|
| Events | 48 | 48 | 1147 | 1147 |
| Mean net/event | −0.05% | −0.27% | −0.46% | −0.69% |
| Sum of event P&L | −$44 | −$261 | −$10530 | −$15746 |
| Daily event P&L t-statistic | -0.14 | -0.81 | -4.90 | -7.19 |
| Worst end-of-day event drawdown | −$489 | −$599 | −$10530 | −$15746 |
| Winners | 27 | 24 | 479 | 438 |
| Mean winner | +1.47% | +1.43% | +2.20% | +2.18% |
| Losers | 21 | 24 | 668 | 709 |
| Mean loser | −1.99% | −1.97% | −2.37% | −2.46% |

Primary gross averaged +0.33%, with a whole-day
bootstrap interval of −0.32% to
+1.00%. The required positive lower
gross bound fails. Control gross averaged −0.10%
with an interval of −0.28% to
+0.09%. These are ordinary descriptive
intervals, not corrections for the extensive adaptive search.

## Later development and on-time checks

| 2013–2016 | Primary | Control |
|---|---:|---:|
| Events | 14 | 334 |
| Active dates | 14 | 267 |
| Gross mean | +1.47% | +0.04% |
| Net mean 1× | +1.06% | −0.34% |
| Net mean 2× | +0.82% | −0.58% |

The primary required 150 events on 90 dates overall and 40
events in the later block. It had 48 and 14.
Its later positive net does not overcome the sample failure
or the later gross return below +3%. Its stressed mean exceeds
the control in both blocks, passing that incremental requirement,
while the other primary gates fail. The control cannot advance.

Every primary entry was on time. The control has
1 late entry; restricting it to 10:00 leaves
1146 events at −0.46% and
−0.69% net. Its later block has no late
entries. Primary full and on-time samples coincide, and the
gate decision is unchanged in both versions. The primary is
also the exact saved-row subset of the control.

6 primary targets and 85
control targets exceed five percent of entry-bar volume.
The study ignores this execution cap; the portfolio would
apply it. These results do not establish executable $2,000
positions at the assumed opening price.

## Annual event means

| Year | Primary events | Primary net 1× | Primary net 2× | Control events | Control net 1× | Control net 2× |
|---|---:|---:|---:|---:|---:|---:|
| 2003 | 0 | N/A | N/A | 17 | −0.77% | −1.01% |
| 2004 | 1 | −2.63% | −2.91% | 61 | −0.46% | −0.67% |
| 2005 | 5 | −2.17% | −2.43% | 77 | −0.92% | −1.15% |
| 2006 | 3 | +0.58% | +0.42% | 65 | −0.70% | −0.89% |
| 2007 | 4 | +0.08% | −0.07% | 111 | −0.52% | −0.73% |
| 2008 | 6 | −1.94% | −2.13% | 97 | −0.68% | −0.92% |
| 2009 | 9 | +0.30% | +0.07% | 121 | −0.42% | −0.66% |
| 2010 | 4 | +0.65% | +0.38% | 90 | −0.45% | −0.69% |
| 2011 | 2 | +0.34% | +0.06% | 94 | −0.44% | −0.66% |
| 2012 | 0 | N/A | N/A | 80 | −0.03% | −0.25% |
| 2013 | 3 | +0.50% | +0.17% | 81 | −0.31% | −0.54% |
| 2014 | 3 | −0.05% | −0.28% | 81 | −0.84% | −1.08% |
| 2015 | 4 | +1.54% | +1.33% | 74 | +0.21% | −0.03% |
| 2016 | 4 | +1.83% | +1.62% | 98 | −0.36% | −0.60% |

## Annual event P&L

| Year | Primary 1× | Primary 2× | Control 1× | Control 2× |
|---|---:|---:|---:|---:|
| 2003 | $0 | $0 | −$261 | −$341 |
| 2004 | −$52 | −$58 | −$557 | −$818 |
| 2005 | −$216 | −$242 | −$1415 | −$1754 |
| 2006 | $35 | $25 | −$901 | −$1154 |
| 2007 | $7 | −$6 | −$1138 | −$1603 |
| 2008 | −$232 | −$255 | −$1318 | −$1773 |
| 2009 | $54 | $13 | −$1014 | −$1598 |
| 2010 | $52 | $30 | −$812 | −$1233 |
| 2011 | $13 | $2 | −$825 | −$1238 |
| 2012 | $0 | $0 | −$46 | −$404 |
| 2013 | $30 | $10 | −$487 | −$869 |
| 2014 | −$2 | −$16 | −$1363 | −$1741 |
| 2015 | $123 | $106 | $315 | −$39 |
| 2016 | $145 | $129 | −$706 | −$1181 |

Dollar diagnostics multiply each saved net event return by
its whole-share notional and sum by date, including zero-event
sessions throughout the registered period. They ignore account
capital conflicts. These are isolated event diagnostics,
not measured account returns or portfolio drawdowns. Mean
notionals were $1991.38 primary and
$1990.55 control against the $2,000 target.

Mean baseline round-trip costs were
+0.38% primary and
+0.36% control.
Doubled slippage leaves fees and commissions unchanged.

## Method and research limits

Tests passed for the print-size integer boundary, transaction
persistence, narrow-range and breakout gates, fixed decision
time, exact control subset, future prices and counts, missing
data, both prefix replays, next-minute expiry and the timed
market exit. Repository rules, strategy loading, Ruff and import
contracts passed. Empirical session replays passed
47 times for the primary and
895 for the control.

The regular event study marks the horizon with a minute
close and estimates both cost legs from the entry bar. The
portfolio uses actual simulated fills, participation, expiry
and a closing-auction fallback. Those differences are explicit
in the hypothesis and tests. Failed gates prevented a portfolio
run, so its performance remains unmeasured. Minute opening
prices do not prove attainable quotes, depth or retail latency.

Volume/count does not identify a parent order, institution
or signed demand. The filter improves this fixed comparison
without meeting the desired return or evidence bars. The
later positive subset cannot select a different period or
holding horizon after the fact. This is adaptive research
with extensive prior looks and no globally pristine-validation
claim.

The earlier accidental documentation-sample post-seal exposure
remains in `docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`.
This registration follows that incident and makes no claim
of zero historical post-seal exposure. No sample value was
used here. These runs loaded only the registered development
period. No new post-seal lookup, sealed-folder access, raw
write, download, rebuild or validation run occurred. Every
numerical measurement above derives from the saved manifests,
study summaries and event tables.
