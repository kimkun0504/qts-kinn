# Late rally selloff

## Verdict

Park. The registered pattern produced nine events on nine dates,
short of 150 events on 90 dates. The 2013–2016 block produced
six against the minimum of 40. Gross return averaged +1.50%
overall and +1.29% in 2013–2016, below the +3% hurdle in
both windows. The net intervals include zero. The strategy
stopped at the development event study.

## Run

- `20261117T142926Z_gpt_late_rally_selloff_5221614c` on 2003-09-10 through 2016-12-30.
  Hypothesis commit `3f9531c`, clean run commit `172dcc6`,
  data build `447e58e098`.
- One new counted `intraday_rebound` trial. The shared family
  count rose to 97, including 9
  previously declared looks.
- All 9 study entries were on the intended next
  minute and all 9 lookahead replays passed. Each event
  had a different security identifier.

| Study window to the close | Events | Sessions with events | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 9 | 9 | +1.50% | +0.82% | +0.41% |
| 2013–2016 | 6 | 6 | +1.29% | +0.62% | +0.19% |

| Full development | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| 95% day-clustered interval for mean net | −0.39% to +2.10% | −0.82% to +1.74% |
| Daily P&L t-statistic | 1.18 | 0.61 |
| Worst end-of-day drawdown | −$52 | −$59 |
| Total modeled net P&L | +$146 | +$74 |

The 95% day-clustered gross interval was +0.37% to +2.70%.
With nine actual event dates this bootstrap has little evidence
about unobserved conditions. The two cost cases use identical
IBKR Pro Tiered fees. The study measures the return to the
official close when available and estimates both marketable
legs using entry-bar conditions. Dollar statistics sum the
modeled independent events over the
3,352 development sessions,
including sessions with zero events.

## Development by year

| Year | Events | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: |
| 2003 | 0 | — | — |
| 2004 | 1 | −0.42% | −0.73% |
| 2005 | 1 | +4.05% | +3.81% |
| 2006 | 0 | — | — |
| 2007 | 0 | — | — |
| 2008 | 1 | +0.01% | −0.52% |
| 2009 | 0 | — | — |
| 2010 | 0 | — | — |
| 2011 | 0 | — | — |
| 2012 | 0 | — | — |
| 2013 | 1 | −0.89% | −1.70% |
| 2014 | 0 | — | — |
| 2015 | 3 | +1.56% | +1.15% |
| 2016 | 2 | −0.06% | −0.28% |

## Limits

The turn before the closing auction appeared too infrequently
to assess a persistent effect. The bars cannot show which
traders reduced exposure or if they faced a deadline. The
official closing mark is observable in the historical data and
does not establish auction fill price or priority for this
strategy. Tests cover exact checkpoint bars, early closes,
prefix replay, next-minute expiry, and same-session auction
exit. Portfolio testing and validation were skipped. The
holdout stayed sealed.
