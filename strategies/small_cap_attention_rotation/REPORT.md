# Small-cap attention rotation

## Verdict

Park. One event on one date met the signal during development.
The minimum was 150 events on 90 dates, including at least 40
events in 2013–2016. The later block had no events. The observed
event lost 2.66% gross at the registered one-hour horizon. One
observation cannot establish a day-clustered confidence bound
or a return estimate suitable for screening. The strategy
stopped after the event study.

## Run

- `20261117T142033Z_gpt_small_cap_attention_rotation_e3d593b9` on 2003-09-10 through 2016-12-30.
  Hypothesis commit `3562acb`, clean run commit `3647f4f`,
  data build `447e58e098`.
- One counted trial in `small_cap_attention_rotation`.
  Related turnover, opening momentum and cross-stock
  studies are recorded in the hypothesis.
- The observed entry was on the intended next clock minute
  and the lookahead replay passed. The target share count
  exceeded 5% of entry-bar volume. The independent event
  study reports the full target size. The engine would
  cap participation in a portfolio.

| Study window at 60 minutes | Events | Sessions with events | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 1 | 1 | −2.66% | −3.03% | −3.23% |
| 2013–2016 | 0 | 0 | — | — | — |

| Full development | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| Daily P&L t-statistic | −1.00 | −1.00 |
| Worst end-of-day drawdown | −$61 | −$65 |
| Total modeled net P&L | −$61 | −$65 |

The daily t-statistic is mechanically −1 because only one
session lost money and all other sessions had zero P&L.
The dollar metrics sum the modeled event across the
3,352 development sessions.
Both cost levels use IBKR Pro Tiered fees and estimate
both marketable legs using the entry bar. The study's
mark at one hour uses the last observed bar at or before
the horizon.

## Development by year

| Year | Events | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: |
| 2003 | 0 | — | — |
| 2004 | 0 | — | — |
| 2005 | 0 | — | — |
| 2006 | 0 | — | — |
| 2007 | 0 | — | — |
| 2008 | 1 | −3.03% | −3.23% |
| 2009 | 0 | — | — |
| 2010 | 0 | — | — |
| 2011 | 0 | — | — |
| 2012 | 0 | — | — |
| 2013 | 0 | — | — |
| 2014 | 0 | — | — |
| 2015 | 0 | — | — |
| 2016 | 0 | — | — |

## Limits

The combination of three leadership events and a later
tradable laggard was too rare in the frozen definition.
The data cannot distinguish shared attention from unrelated
news or other common exposures. The study therefore yields
an eligibility failure and one hypothetical return. Tests
cover the prior cohort, leader breadth, temporal separation,
signal-time bar availability, next-minute expiry and the
same-session exit. Validation and the sealed holdout were
outside this run.
