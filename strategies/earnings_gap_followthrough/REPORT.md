# Earnings gap follow-through

## Verdict

Park. The only preregistered variant cleared the sample gates, then
missed the gross return, stressed net return, and confidence gates.
Average gross return to the close was +0.39% against the +3% minimum.
The day-clustered gross interval crossed zero. The development
portfolio and validation were skipped under the preregistered rule.

## Run

- `20261117T042527Z_gpt_earnings_gap_followthrough_534ec267`, Kinn event
  study, 2003-09-10 through 2016-12-30. Hypothesis commit `b13a3ef`,
  clean run commit `4cc2825`, data build `447e58e098`.
- Family `opening_gap_continuation`. One trial, with zero prior trials
  in the run manifest for this family. The hypothesis records the
  related broad gap and dated disclosure research.
- Form 8-K input `2578b76aa1`, version `form8k-1`. An Item 2.02
  filing dated before the entry session qualified only when the
  registered price and turnover conditions also held.
- All 560 events entered at the intended minute across 424 sessions.
  Kinn recorded 424 lookahead replay checks. Position size was
  liquidity-limited for about 6% of events.

| Window | Events | Active sessions | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 560 | 424 | +0.39% | −0.02% | −0.32% |
| 2013–2016 | 197 | 146 | +0.15% | −0.29% | −0.60% |

| Full development | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| 95% day-clustered interval for mean net | −0.46% to +0.41% | −0.77% to +0.11% |
| Daily P&L t-statistic | −0.10 | −1.42 |
| Worst end-of-day drawdown | −$3,025 | −$4,439 |
| Total modeled net P&L | −$243 | −$3,620 |

The 95% day-clustered gross interval was −0.05% to +0.83%. Both
cost cases use IBKR Pro Tiered fees. Only modeled slippage doubles
in the stress case. Daily dollar P&L sums the events at their modeled
fill sizes and includes zero-event trading sessions. The daily
statistics and drawdowns describe an independent-event series.
Portfolio capital constraints were never tested.

## Development by year

| Year | Events | Net mean at 1× | Net mean at 2× | Net P&L at 1× | Net P&L at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | $0 | $0 |
| 2004 | 11 | −0.58% | −0.88% | −$131 | −$197 |
| 2005 | 28 | +0.74% | +0.42% | +$412 | +$236 |
| 2006 | 52 | +0.26% | +0.00% | +$275 | +$2 |
| 2007 | 32 | −0.06% | −0.31% | −$45 | −$206 |
| 2008 | 54 | −0.83% | −1.11% | −$891 | −$1,191 |
| 2009 | 61 | −0.08% | −0.44% | −$94 | −$529 |
| 2010 | 36 | +1.23% | +0.93% | +$885 | +$671 |
| 2011 | 40 | +0.98% | +0.69% | +$776 | +$546 |
| 2012 | 49 | −0.32% | −0.59% | −$307 | −$579 |
| 2013 | 50 | −0.92% | −1.21% | −$918 | −$1,208 |
| 2014 | 43 | −0.67% | −0.98% | −$581 | −$841 |
| 2015 | 49 | +0.74% | +0.40% | +$727 | +$388 |
| 2016 | 55 | −0.32% | −0.65% | −$353 | −$713 |

## Interpretation

The rule measures continuation after an opening gap associated with an
available earnings filing. The date-only input makes filings usable
from the first session after filing and can miss the first reaction.
The fraction of gaps caused by the filing is unknown. Measuring an
earnings beat would require the release figures and analyst consensus
as it stood before publication. Market entry and auction exit use
modeled execution on historical bars.

Strategy tests cover the eligibility and minute-availability rules.
The platform Form 8-K tests cover next-session availability, manifest
attribution and replay with the filing hidden on its own date.
