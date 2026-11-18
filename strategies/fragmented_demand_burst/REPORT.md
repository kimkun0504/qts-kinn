# Fragmented demand burst

## Verdict: park

The primary smaller-print rule produced no events. Its count-burst
control produced nine events on nine dates, averaging −1.01%
net at base costs and −1.30% with doubled slippage.
The primary fails the sample gates and supplies no return estimate.
The control is ineligible to replace it and also fails the sample
and return gates. No portfolio or validation run was performed;
no threshold, stock selection or clock time was changed.

## Runs and attribution

| Variant | Run ID | Events | Active dates | Replays |
| --- | --- | ---: | ---: | ---: |
| Primary smaller-print subset | `20261118T220607Z_gpt_fragmented_demand_burst_6c61b0c0` | 0 | 0 | 0 |
| Count-burst control | `20261118T220825Z_gpt_fragmented_demand_burst_c8e69d01` | 9 | 9 | 9 |

Both are completed Kinn studies on 2003-09-10 through 2016-12-30.
Hypothesis commit `d74dab5`; clean implementation/run commit
`bb37883`; agent `gpt`, data build `447e58e098`,
`ibkr_pro_tiered`, $20,000 account and $2,000 target.

Two additional trials in `big_prints` bring its total to
54: 49 earlier declared looks and five counted
run-store trials. Related volume, momentum and rebound research
remains part of the broader adaptive search.

## Frozen study gate assessment

| Gate | Primary observation | Decision |
| --- | --- | --- |
| 150 events on 90 dates overall | 0 events, 0 dates | Fail |
| 40 events in 2013–2016 | 0 | Fail |
| Gross mean >= +3% in both blocks | Not estimable | No support |
| Positive stressed mean in both blocks | Not estimable | No support |
| Positive full gross day-cluster lower bound | Not estimable | No support |
| Primary stressed mean above control in both blocks | Empty primary | Fail |

The primary event set is an empty subset of the control. Matching
is therefore vacuous and demonstrates no improvement from the
smaller-print filter. No claim is made that rejecting negative
control events establishes a successful filter.

## Control diagnostics, not a portfolio

| Window | Events | Dates | Gross mean | Net mean, 1× | Net mean, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 9 | 9 | −0.56% | −1.01% | −1.30% |
| 2013–2016 | 2 | 2 | −1.53% | −1.97% | −2.26% |

| Full control | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| Total modeled event P&L | −$181 | −$233 |
| Daily P&L t-statistic | -0.86 | -1.08 |
| Worst end-of-day drawdown | −$230 | −$278 |
| 95% day-cluster interval for mean net | −3.20% to +1.06% | −3.47% to +0.78% |
| Winners | 4 | 4 |
| Mean winner | +2.33% | +2.01% |
| Losers | 5 | 5 |
| Mean loser | −3.68% | −3.95% |

Full gross day-cluster interval: −2.79% to
+1.56%. The control's mean target notional
was $1,993. Mean round-trip fees were
+0.15% of notional; modeled base slippage
+0.29%. At 2×, only slippage doubles.

Every control entry occurred at the intended next clock minute,
so on-time and full-sample diagnostics coincide. One control
target exceeded 5% of entry-bar volume. The study did not apply
that capacity limit. There were no primary events to audit.

Daily dollar P&L sums event return times target shares times
entry price on each session, including zero-event sessions from
the run manifest. Drawdown is the decline in cumulative dollar
event P&L from its prior peak, including the initial zero.
These describe independent-event diagnostics; account capital,
buying-power conflicts and timed portfolio liquidation were
never tested.

## Control results by development year

The primary has zero events in every year; its means, t-statistics,
drawdowns and conditional winner/loser means are not estimable.

| Year | Control events | Net mean, 1× | Net mean, 2× | Event P&L, 1× | Event P&L, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | $0 | $0 |
| 2004 | 2 | −1.97% | −2.18% | −$78 | −$87 |
| 2005 | 2 | −1.91% | −2.12% | −$76 | −$85 |
| 2006 | 0 | — | — | $0 | $0 |
| 2007 | 1 | −3.35% | −3.57% | −$67 | −$71 |
| 2008 | 0 | — | — | $0 | $0 |
| 2009 | 1 | +1.83% | +1.53% | $36 | $30 |
| 2010 | 0 | — | — | $0 | $0 |
| 2011 | 1 | +4.14% | +3.48% | $83 | $70 |
| 2012 | 0 | — | — | $0 | $0 |
| 2013 | 0 | — | — | $0 | $0 |
| 2014 | 0 | — | — | $0 | $0 |
| 2015 | 0 | — | — | $0 | $0 |
| 2016 | 2 | −1.97% | −2.26% | −$79 | −$90 |

## Bias, execution and data limits

All empirical metrics above derive only from the two saved
run manifests, study summaries and events tables, using the
registered r_60 horizon. No fresh raw/panel query or scratch
backtest supplies a number.

Focused strategy/repository tests passed, including exact
integer count/size comparisons, missing counts, prior share-count
screening, all clock prefixes around the event, deliberate
future-count cheating, future-price/count perturbations,
primary/control subset identity and next-minute entry expiry.
Lint, formatting and import contracts passed. Synthetic replay
does not establish attainable quotes.

Market cap divided by prior adjusted price is an estimated
outstanding-share proxy, not free float. Aggregate transactions
have no signed demand or investor identity. Missing minutes and
counts remain missing. The normal study ignores order expiry,
capital conflicts and participation, prices both cost legs
from the entry bar, and uses a horizon close rather than the
portfolio's exit open. Both cost cases share the same modeled
entry and exit observations.

The rule was registered after earlier family results and the
documented documentation-sample exposure. This is adaptive
research with many prior looks, not globally pristine validation.
Neither run loaded validation or sealed-holdout market dates.
The candidate stays parked.

## Trial-accounting addendum

After this report's original write-up, Claude branch commit
`d67cdc15860f8e72207e40dbdc02d8a7e3adf5ec` was fetched.
Its follow-up 17 declares two further `big_prints` looks,
raising that earlier declared baseline from 49 to 51.
With the five counted run-store trials, the known family
total is now 56. The original manifests retain their
49-prior-look snapshot; no returns or selection gates change.
