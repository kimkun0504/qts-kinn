# Smaller-print selloff exhaustion

**Verdict: park.** The primary had only 1 event on
1 date, in 2008, and none in 2013–2016. Its
+7.47% base net and +6.93%
stressed return describe one outcome. They do not establish an
alpha. The sample, later-period and confidence-bound gates fail.
No portfolio or validation run was made. No threshold changed.

The fixed control had 333 events on 256 dates,
averaging +2.64% net at base costs and
+2.18% at doubled slippage overall. In
2013–2016 its 59 events averaged
+0.29% and −0.14%.
Its later gross mean was +0.96%, below +3%, and
stressed net was negative. The control was never eligible for
selection; its older positive mean cannot promote it after the fact.

## Runs and frozen selection

- Primary: `20261118T153853Z_gpt_fragmented_selloff_exhaustion_03147c02` (`development`).
- Control: `20261118T154041Z_gpt_fragmented_selloff_exhaustion_36df564b` (`development_control`).
- Both: 2003-09-10 through 2016-12-30, data build
  `447e58e098`, clean commit `ce889d2`. Hypothesis commit
  `55b62c7` preceded implementation and every empirical run.
- Two new trials in `intraday_rebound`, now 109
  including nine declared earlier looks. The family began this
  program with 48 trials. Related search is acknowledged in
  HYPOTHESIS.md; this is not an independent first rebound look.
- Saved primary rows exactly match control rows on the common
  event, including entry, return and cost fields. The primary
  is an exact subset. No later event could rescue an excluded stock.

## Full development at r_120

| Measurement | Primary 1× | Primary 2× | Control 1× | Control 2× |
|---|---:|---:|---:|---:|
| Events | 1 | 1 | 333 | 333 |
| Mean net/event | +7.47% | +6.93% | +2.64% | +2.18% |
| Sum of event P&L | $149 | $139 | $17577 | $14488 |
| Daily event P&L t-statistic | 1.00 | 1.00 | 3.39 | 2.85 |
| Worst end-of-day event drawdown | $0 | $0 | −$1992 | −$2077 |
| Winners | 1 | 1 | 203 | 196 |
| Mean winner | +7.47% | +6.93% | +9.47% | +9.33% |
| Losers | 0 | 0 | 130 | 137 |
| Mean loser | N/A | N/A | −8.02% | −8.06% |

Gross means were +8.44% for the primary and
+3.34% for the control. No clustered interval is
available for the single primary date. The control gross
day-clustered interval was +1.81% to
+4.73%. Its positive full-period lower
bound does not resolve the later-period weakness.

The primary required 150 events on 90 dates overall and 40
events in 2013–2016. Its later means and required incremental
advantage over the control there are unmeasurable. One observed
full-period winner does not establish a filter advantage.
Zero observed primary drawdown is equally uninformative.

All primary and control entries occurred on the next clock
minute. Their on-time subsets equal their full studies in
both development blocks; the same failures apply. Capacity
remains separate: the sole primary target and
9 control targets exceed five percent of
entry-bar volume. Actual participation would reduce those
fills. The primary's one-event result is not a measured
executable $2,000 portfolio.

## Annual event means

| Year | Primary events | Primary net 1× | Primary net 2× | Control events | Control net 1× | Control net 2× |
|---|---:|---:|---:|---:|---:|---:|
| 2003 | 0 | N/A | N/A | 6 | −2.02% | −2.40% |
| 2004 | 0 | N/A | N/A | 15 | +5.95% | +5.47% |
| 2005 | 0 | N/A | N/A | 12 | +4.09% | +3.78% |
| 2006 | 0 | N/A | N/A | 16 | +1.63% | +1.25% |
| 2007 | 0 | N/A | N/A | 30 | +7.10% | +6.56% |
| 2008 | 1 | +7.47% | +6.93% | 117 | +3.79% | +3.26% |
| 2009 | 0 | N/A | N/A | 30 | +1.42% | +1.03% |
| 2010 | 0 | N/A | N/A | 8 | +3.19% | +2.87% |
| 2011 | 0 | N/A | N/A | 25 | −1.87% | −2.30% |
| 2012 | 0 | N/A | N/A | 15 | +2.20% | +1.74% |
| 2013 | 0 | N/A | N/A | 9 | −0.38% | −0.79% |
| 2014 | 0 | N/A | N/A | 15 | −0.85% | −1.22% |
| 2015 | 0 | N/A | N/A | 19 | +1.34% | +0.85% |
| 2016 | 0 | N/A | N/A | 16 | +0.47% | +0.06% |

## Annual event P&L

| Year | Primary 1× | Primary 2× | Control 1× | Control 2× |
|---|---:|---:|---:|---:|
| 2003 | $0 | $0 | −$243 | −$288 |
| 2004 | $0 | $0 | $1783 | $1638 |
| 2005 | $0 | $0 | $982 | $909 |
| 2006 | $0 | $0 | $518 | $397 |
| 2007 | $0 | $0 | $4263 | $3936 |
| 2008 | $149 | $139 | $8860 | $7622 |
| 2009 | $0 | $0 | $852 | $620 |
| 2010 | $0 | $0 | $507 | $456 |
| 2011 | $0 | $0 | −$936 | −$1153 |
| 2012 | $0 | $0 | $656 | $517 |
| 2013 | $0 | $0 | −$69 | −$143 |
| 2014 | $0 | $0 | −$248 | −$360 |
| 2015 | $0 | $0 | $505 | $319 |
| 2016 | $0 | $0 | $148 | $17 |

Dollar diagnostics multiply each saved net event return by
its whole-share notional and sum by date, including registered
zero-event sessions. Capital conflicts are ignored. These are
event diagnostics, not measured account returns or portfolio
drawdowns. Mean notionals were $2000.00
for the primary and $1993.90 for the control.

Mean baseline round-trip costs were
+0.97% for the primary
and +0.70% for the
control. Doubled slippage leaves fees and commissions unchanged.

## Availability, execution and interpretation

Synthetic tests passed for the score, integer fragmentation
boundaries, first-base and no-later-rescue rules, exact subset,
missing bars and counts, both prefix replays, next-minute
expiry and the two-hour portfolio exit. Repository rules,
strategy loading, Ruff and import contracts passed. The real
runs passed 1 primary and
256 control session replays.

The regular event study marks the horizon with a minute
close and estimates both cost legs from the entry bar. The
portfolio would use actual simulated exit fills, participation
and expiry, with a closing-auction fallback. These differences
are explicit in the hypothesis and tests. Failed gates
prevented a portfolio run, so its results remain unmeasured.
Quotes, depth, halt states and auction allocation are unverified.

Volume/count does not establish signed flow, parent orders
or trader identity. This follow-up does not support the
registered fragmentation filter. The control's positive older
average is hypothesis-generating and does not overcome its
weak 2013–2016 block. Earlier related validation outcomes were
already known; no globally pristine validation claim is made.

The earlier documentation-sample exposure remains recorded in
`docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`.
This rule was registered after that incident and does not
claim zero historical post-seal exposure. No sample values
were used here. These studies loaded only their registered
development period. No new post-seal lookup, sealed-folder
access, validation run, raw write, rebuild or download occurred.
Every numerical measurement above derives from the two saved
manifests, study summaries and event tables.
