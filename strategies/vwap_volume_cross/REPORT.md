# VWAP cross with a turnover surge

## Verdict

Park. The primary high-turnover rule produced 1,843 events on
1,350 development dates, meeting the sample bars. At the registered
one-hour horizon it lost 0.10% gross, 0.65% at base costs, and
1.01% at doubled slippage. The gross confidence interval included
zero. The 2013–2016 result also missed the gross and stressed
return gates. No portfolio or validation run followed.

The ordinary-turnover comparison lost 0.16% gross and 0.69% at
base costs. The high-turnover point estimate offers little
separation from this group. Both registered definitions lost after
costs. Their different stock-dates and exposures preclude a causal
estimate of the effect of increased turnover.

## Runs and definitions

- Primary `20261117T192448Z_gpt_vwap_volume_cross_35ae5f0d`, config `development`.
- Ordinary comparison `20261117T192558Z_gpt_vwap_volume_cross_0c72bcd1`, config
  `development_ordinary`.
- Both are clean event studies on 2003-09-10 through 2016-12-30,
  data build `447e58e098`, commit `28e4990`. Hypothesis commit
  `b620e74` preceded both. The primary finished before the
  comparison began. Both used the pre-registered first eligible
  price-and-liquidity setup.
- These add two `intraday_rebound` trials. The shared family
  count at reporting is 99, including nine
  earlier declared looks. Kinn passed 1,350
  primary and 351 comparison lookahead replays.

A cross block must finish at least 2% above VWAP estimated through
the preceding block's close. Entry waits for the following
five-minute block to finish above the same reference. Cross
turnover is divided by the median of the preceding six
five-minute blocks. Surge means at least 3×. Ordinary means
1× through 1.5× inclusive. The position is held one hour
from the next clock minute's modeled entry.

Kinn's current session interface carries today's bars and prior
daily summaries. It does not supply prior sessions' same-clock
volumes. The test therefore uses the preceding 30 minutes as
its baseline. This is a turnover acceleration test and can be
affected by time of day. VWAP uses minute closes times volumes
and is approximate. A trade-weighted price within each minute
is unobserved in the strategy view.

## One-hour development results

| Group and window | Events | Active dates | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Surge, full development | 1,843 | 1,350 | −0.10% | −0.65% | −1.01% |
| Surge, 2013–2016 | 471 | 368 | +0.16% | −0.36% | −0.69% |
| Ordinary, full development | 530 | 351 | −0.16% | −0.69% | −1.02% |
| Ordinary, 2013–2016 | 119 | 91 | +0.11% | −0.44% | −0.77% |

| Full-period day-clustered 95% interval | Surge | Ordinary |
| --- | ---: | ---: |
| Gross mean | −0.27% to +0.06% | −0.52% to +0.20% |
| Net mean at 1× | −0.82% to −0.49% | −1.06% to −0.33% |
| Net mean at 2× | −1.18% to −0.84% | −1.39% to −0.65% |

The groups share 185 event dates and have no
overlapping security-days. Each configuration uses identical
universe, price conditions, entry timing, target size, holding
time and costs.

## Entry expiry sensitivity

The event-study entry function takes the first observed bar
after a signal even when an order would have expired. It entered
28 primary and
7 comparison events after expiry.
Each registered gate was reapplied to the entries on the next
clock minute. The result still fails.

| Next-minute entries | Events | Active dates | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Surge, full development | 1,815 | 1,331 | −0.09% | −0.65% | −1.00% |
| Surge, 2013–2016 | 467 | 364 | +0.15% | −0.37% | −0.70% |
| Ordinary, full development | 523 | 347 | −0.17% | −0.70% | −1.03% |
| Ordinary, 2013–2016 | 117 | 89 | +0.09% | −0.47% | −0.80% |

## Independent event P&L

| Group and cost | Daily P&L t-statistic | Worst end-of-day drawdown | Total modeled net P&L |
| --- | ---: | ---: | ---: |
| Surge, 1× | −7.62 | −$24,412 | −$23,978 |
| Surge, 2× | −11.29 | −$37,331 | −$37,007 |
| Ordinary, 1× | −3.54 | −$7,821 | −$7,305 |
| Ordinary, 2× | −5.01 | −$11,160 | −$10,798 |

These statistics sum independent $2,000-target study entries and
include zero-event days across 3,352 sessions. They do not enforce
account capital constraints. About
24% of primary target orders
and 24% of comparison target
orders exceeded the 5% entry-bar participation cap. Actual portfolio
fills would depend on that cap, reservations and expiry.
Both cases use IBKR Pro Tiered fees. Only slippage doubles.

The study measures the exit using the last observed bar at or
before the one-hour horizon, capped at the official close. It
estimates both marketable legs from entry-bar conditions. Execution
at a live bid or ask and executable size remain unverified.

## Results by year at the registered horizon

| Year | Surge events | Surge net at 1× | Surge net at 2× | Ordinary events | Ordinary net at 1× | Ordinary net at 2× |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2003 | 26 | −0.16% | −0.63% | 5 | +2.70% | +2.44% |
| 2004 | 176 | −0.68% | −1.06% | 28 | −0.93% | −1.43% |
| 2005 | 181 | −0.37% | −0.72% | 20 | −1.56% | −1.88% |
| 2006 | 153 | −1.02% | −1.38% | 18 | −0.87% | −1.20% |
| 2007 | 154 | −1.14% | −1.49% | 32 | −0.00% | −0.30% |
| 2008 | 213 | −1.16% | −1.54% | 185 | −0.73% | −1.04% |
| 2009 | 162 | −0.53% | −0.88% | 75 | −0.92% | −1.25% |
| 2010 | 112 | −1.05% | −1.39% | 7 | −0.05% | −0.36% |
| 2011 | 107 | −0.49% | −0.88% | 25 | −1.03% | −1.39% |
| 2012 | 88 | −0.08% | −0.41% | 16 | −1.47% | −1.86% |
| 2013 | 101 | −0.26% | −0.58% | 8 | −2.12% | −2.63% |
| 2014 | 120 | −0.63% | −0.95% | 25 | +0.41% | +0.10% |
| 2015 | 126 | −0.45% | −0.77% | 39 | −0.98% | −1.29% |
| 2016 | 124 | −0.09% | −0.44% | 47 | −0.17% | −0.49% |

## Checks and scope

Synthetic tests cover the common first setup, turnover
classification, rejection of later substitute signals, exact
block-end observations, premarket exclusion, replay with later
bars hidden, next-minute expiry, the one-hour exit, and unchanged
validation parameters. Strategy tests, the lookahead canaries,
repository rules, Ruff and the import contracts passed.

This result applies to the registered block-based setup, including
its 2% cross threshold and confirmation delay. The first impulse
has already occurred at entry. It cannot establish the return from
a trade submitted before the impulse or from immediate news receipt.
The holdout beginning 2023-11-09 stayed sealed.
