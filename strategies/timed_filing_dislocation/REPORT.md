# Relative dislocation with an as-of-time filing exclusion

## Verdict: park

The new filter failed its registered improvement test in both
development blocks. It removed 24 events that were profitable
on average. The retained study earned +3.64% net at
base costs and +3.17% at doubled slippage, slightly
below the saved baseline. This is an incremental test of an
existing signal; its positive mean is not a new independent alpha.

The study passed the other preregistered sample, gross, stressed
return and full gross confidence gates. The failed comparison
still requires parking. No portfolio or validation run was
performed. No filter, threshold or gate was adjusted.

## Run and reproducibility

- Run `20261119T040929Z_gpt_timed_filing_dislocation_726f534f`,
  completed Kinn event study, 2003-09-10 through 2016-12-30.
- Hypothesis commit `5115892`; clean run commit `a43b9f5`;
  agent `gpt`, data build `447e58e098`.
- Pinned date-level input `2578b76aa1` / `form8k-1` and
  timed input `adba6fd432` / `form8k-timed-1`.
- Saved comparison study:
  `20261118T011256Z_gpt_filing_aware_dislocation_2df4fa72`.
  It uses the same data build, prior-date screen, price rule,
  account settings and cost calibration. No baseline rerun.
- `intraday_rebound`: one new trial, total
  111, including nine earlier declared looks.
  The family began the original brief with 48 trials.
- Account and buying power $20,000; target $2,000 per order;
  ten reservations; 5% participation; `ibkr_pro_tiered`.

Every retained company/date matched the saved baseline exactly
on symbol, decision and entry minute, entry price, shares,
entry-bar volume, fees, slippage and r_120. There were no added
or altered events. Peer baskets include the screened stocks,
so the comparison isolates the filing exclusion.

## Retained and removed event diagnostics

| Development window | Events | Active dates | Gross mean | Net mean, 1× | Net mean, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Saved baseline, full | 257 | 178 | +4.36% | +3.65% | +3.19% |
| Retained, full | 233 | 161 | +4.34% | +3.64% | +3.17% |
| Removed, full | 24 | 23 | +4.52% | +3.80% | +3.37% |
| Saved baseline, 2013–2016 | 45 | 41 | +3.07% | +2.52% | +2.19% |
| Retained, 2013–2016 | 42 | 38 | +3.03% | +2.46% | +2.14% |
| Removed, 2013–2016 | 3 | 3 | +3.64% | +3.26% | +2.99% |

The removed subset's mean was higher than the retained subset
at both costs, overall and in the later block. This screen
does not improve the observed event mean. These small,
nonrandom removed samples cannot establish a causal benefit
from buying a stock with a filing.

## Registered gate assessment

| Gate | Result | Decision |
| --- | --- | --- |
| 150 events on 90 dates overall | 233 on 161 dates | Pass |
| 40 events in 2013–2016 | 42 on 38 dates | Pass |
| Gross mean >= +3% in both blocks | +4.34% full; +3.03% later | Pass |
| Positive stressed mean in both blocks | +3.17% full; +2.14% later | Pass |
| Positive full gross lower confidence bound | +2.22% | Pass |
| Stressed mean above baseline, full | +3.17% versus +3.19% | **Fail** |
| Stressed mean above baseline, 2013–2016 | +2.14% versus +2.19% | **Fail** |

All retained entries were at the next clock minute, so full and
on-time samples coincide. The run recorded 161 signal-day
lookahead checks. Four study targets exceeded 5% of their
entry-bar volume; that limit is not enforced by the normal
event study. There were 233 signals and completed measured
events. These are study events, not newly tested portfolio trades.

## Full retained study risk and distribution

| Diagnostic | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| Total modeled event P&L | $16,903 | $14,746 |
| Daily P&L t-statistic | 3.05 | 2.74 |
| Worst end-of-day drawdown | −$1,475 | −$1,515 |
| 95% day-clustered mean-net interval | +1.56% to +5.82% | +1.12% to +5.33% |
| Winners | 147 | 142 |
| Mean winner | +11.94% | +11.94% |
| Losers | 86 | 91 |
| Mean loser | −10.55% | −10.50% |

Full gross confidence interval: +2.22% to
+6.52%. Mean target notional was $1,993.
Daily P&L sums event net dollars across all sessions in the run
manifest, including zero-event dates. Drawdown is cumulative
dollar event P&L below its prior peak, including the initial zero.
Fees stay fixed in the stress case; only modeled slippage doubles.

The daily event series' stressed annualised Sharpe was
0.75. It is not a capital-constrained portfolio
Sharpe. The earlier date-filtered portfolio failed its own
Sharpe gate, as documented in its report; that old verdict
remains unchanged. This study does not establish a replacement
portfolio or meet the validation goal.

## Retained study by year

| Year | Events | Net mean, 1× | Net mean, 2× | Event P&L, 1× | Event P&L, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 1 | +31.49% | +31.38% | $622 | $619 |
| 2004 | 4 | +8.69% | +8.40% | $694 | $671 |
| 2005 | 4 | −6.56% | −6.83% | −$525 | −$546 |
| 2006 | 9 | +3.68% | +3.39% | $659 | $607 |
| 2007 | 19 | +5.48% | +5.06% | $2,074 | $1,916 |
| 2008 | 119 | +4.30% | +3.71% | $10,199 | $8,798 |
| 2009 | 15 | +0.05% | −0.27% | $17 | −$80 |
| 2010 | 3 | +2.81% | +2.60% | $164 | $152 |
| 2011 | 9 | −3.36% | −3.58% | −$605 | −$644 |
| 2012 | 8 | +9.59% | +9.11% | $1,532 | $1,455 |
| 2013 | 8 | +4.47% | +4.12% | $718 | $662 |
| 2014 | 11 | +3.03% | +2.68% | $667 | $590 |
| 2015 | 15 | +3.87% | +3.58% | $1,157 | $1,070 |
| 2016 | 8 | −2.96% | −3.29% | −$471 | −$525 |

## Availability, tests and material limits

The current-session exclusion is evaluated at the first baseline
event minute using only records with usable_minute <= that minute.
An 8-K arriving later cannot retroactively suppress the signal.
The prior-date filing screen is preserved. Native typed reports
and prefix replay are used; the strategy opens no second data stream.

Focused strategy, configuration-load and repository tests passed.
They cover usability at the exact cutoff, later filings, identity
mismatches, empty items, other-session records, retention of excluded
peers in the benchmark, unchanged baseline signals, full prefixes,
a deliberately cheating end-of-day filing exclusion, next-minute
expiry and timed/auction exits. Lint and import contracts passed.

All empirical diagnostics derive from the saved run manifests
and r_120 event rows. No raw/panel query, scratch simulation,
alternate horizon or later-period strategy evaluation supplies
a result. This run loads no market date after 2016-12-30.

The timed archive excludes unsupported item formats, conflicting
accessions and ambiguous identities. Its observed date envelope
does not certify complete issuer coverage. SEC acceptance may
follow a press release, and its delay is assumed rather than
measured from a real dissemination feed. No qualifying record
does not establish absence of news.

The normal study ignores capital conflicts, entry expiry and
participation; uses a horizon close rather than the portfolio's
timed exit open; and prices both cost legs from the entry bar.
Actual spreads, depth and latency remain unobserved. Static
category, market-cap and identity assumptions remain in the
pre-open panel. The strategy requires no inferred resting-limit
fill.

This registration follows extensive prior adaptive research and
the documented documentation-sample exposure. The validation
years have been used for other definitions and are not globally
pristine. This failed filter receives no validation attempt
or tuning after its result. The holdout stays sealed.
