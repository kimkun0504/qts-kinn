# Equity sale gap reclaim

## Verdict

Park. One event on one date qualified in development, below the
required 150 events on 90 dates. No events qualified in 2013–2016
against the minimum of 40. The event lost 4.38% before costs.
A day-clustered confidence interval cannot be estimated from one
event. The portfolio and validation stages were skipped under
the preregistered sequence.

## Run

- `20261117T141536Z_gpt_equity_sale_gap_reclaim_9d4c3fa0`, event study on 2003-09-10 through
  2016-12-30. Hypothesis commit `fd09fb3`, clean run commit
  `3ccdd57`, data build `447e58e098`.
- Form 8-K input `2578b76aa1`, version
  `form8k-1`. Kinn matched previously dated reports
  to the security identifier and ticker. The selection was based
  on Item 3.02 in the visible report and the registered price path.
- One new `intraday_rebound` trial. The shared family count
  rose to 95, including 9
  declared earlier looks.
- The event entered on the next clock minute and its lookahead
  replay passed. There was no late-entry sensitivity.

| Study window to the close | Events | Sessions with events | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 1 | 1 | −4.38% | −4.62% | −4.72% |
| 2013–2016 | 0 | 0 | — | — | — |

| Full development | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| Daily P&L t-statistic | −1.00 | −1.00 |
| Worst end-of-day drawdown | −$92 | −$94 |
| Total modeled net P&L | −$92 | −$94 |

The daily t-statistic is mechanically −1 because the daily
series contains one negative observation and zeros on the other
sessions. The dollar metrics use the saved event's modeled
notional and the 3,352 development
sessions. Both cost cases use the same IBKR Pro Tiered fees.
The study estimates both marketable legs from the entry bar's
spread and impact inputs. The portfolio engine's auction fill
rules were not tested.

## Development by year

| Year | Events | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: |
| 2003 | 0 | — | — |
| 2004 | 0 | — | — |
| 2005 | 0 | — | — |
| 2006 | 0 | — | — |
| 2007 | 0 | — | — |
| 2008 | 0 | — | — |
| 2009 | 0 | — | — |
| 2010 | 0 | — | — |
| 2011 | 0 | — | — |
| 2012 | 1 | −4.62% | −4.72% |
| 2013 | 0 | — | — |
| 2014 | 0 | — | — |
| 2015 | 0 | — | — |
| 2016 | 0 | — | — |

## Limits

The joint condition of a newly usable filing, a steep opening
gap, partial recovery and active trading supplied too little
evidence to assess the mechanism. The Item 3.02 label carries
no deal price, dilution estimate, cash proceeds or first
announcement timestamp. The result cannot identify why the one
stock opened lower or what determines performance across
equity sales.

Tests cover filing date and identity, overlapping labeled
earnings, the opening recovery, completed-bar replay,
next-minute expiry and the same-day auction exit. The
sealed holdout stayed excluded.
