# Distributed morning selloff

## Verdict

Park. The registered signal passed the sample gates. It averaged
−0.06% gross to the close overall and −1.94% in 2013–2016
against a +3% minimum in both windows. Stressed net returns were
negative in both windows, and the full-period gross confidence
interval crossed zero. The strategy stopped at the
development event study.

## Run

- `20261117T142444Z_gpt_distributed_morning_selloff_486c5e36` on 2003-09-10 through 2016-12-30.
  Hypothesis commit `8b6e66c`, clean run commit `aea819e`,
  data build `447e58e098`.
- One new `intraday_rebound` trial. The shared family count
  rose to 96, including 9
  declared earlier looks.
- Kinn recorded 158 successful lookahead replays.
  The 233 events covered 210
  distinct security identifiers.

| Study window to the close | Events | Sessions with events | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 233 | 158 | −0.06% | −0.47% | −0.73% |
| 2013–2016 | 62 | 43 | −1.94% | −2.34% | −2.58% |
| Next-minute entries only | 232 | 157 | −0.07% | −0.48% | −0.74% |
| 2013–2016, next-minute entries only | 61 | 42 | −1.99% | −2.39% | −2.63% |

Kinn's event study counts the first observed bar after the
decision. It counted one entry two clock minutes after the
signal, past the order expiry. Restricting to next-minute
entries leaves the verdict unchanged.

| Full development | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| 95% day-clustered interval for mean net | −2.10% to +1.02% | −2.36% to +0.77% |
| Daily P&L t-statistic | −0.59 | −0.90 |
| Worst end-of-day drawdown | −$4,547 | −$5,243 |
| Total modeled net P&L | −$2,204 | −$3,409 |

The full-period 95% day-clustered gross interval was
−1.67% to +1.43%. Dollar statistics sum independent study
events across 3,352 sessions,
including days with no events. Both costs use the same
IBKR Pro Tiered fees. The study estimates each marketable
leg from the entry bar. About
13% of target sizes
exceeded 5% of their entry-bar share volume. The portfolio
engine would cap fills at that participation rate.

## Development by year

| Year | Events | Net mean at 1× | Net mean at 2× | Net P&L at 1× | Net P&L at 2× |
| --- | ---: | ---: | ---: | ---: |
| 2003 | 3 | −0.39% | −0.63% | −$23 | −$37 |
| 2004 | 4 | +2.33% | +2.04% | +$187 | +$164 |
| 2005 | 3 | +4.98% | +4.59% | +$296 | +$273 |
| 2006 | 7 | +0.85% | +0.51% | +$121 | +$73 |
| 2007 | 18 | −0.77% | −1.12% | −$276 | −$400 |
| 2008 | 82 | −0.14% | −0.36% | −$239 | −$593 |
| 2009 | 31 | +0.09% | −0.17% | +$57 | −$105 |
| 2010 | 5 | −3.77% | −4.16% | −$376 | −$414 |
| 2011 | 12 | +2.13% | +1.83% | +$510 | +$436 |
| 2012 | 6 | +3.62% | +3.25% | +$434 | +$389 |
| 2013 | 10 | −2.40% | −2.67% | −$480 | −$532 |
| 2014 | 8 | −1.65% | −1.87% | −$262 | −$297 |
| 2015 | 16 | −4.40% | −4.65% | −$1,406 | −$1,487 |
| 2016 | 28 | −1.34% | −1.57% | −$748 | −$881 |

## Interpretation

In 2008 there were 82 of the
233 events, averaging
−0.36% at 2×. Excluding 2008
as a descriptive check leaves 151
events at −0.93% at 2×.
The loss persists before modeled costs in the full study.
Prices between the checkpoints and the reasons for the
selling remain unverified.

Tests cover exact completed checkpoints, the maximum share
of the decline attributable to one interval, prefix replay,
next-minute expiry and auction exit. The study did not
advance to the portfolio or validation. The holdout stayed
sealed.
