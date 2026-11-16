# New listing drift

**Verdict: park.** The point-in-time stock selector combined observed listing age with
an early price rise and rapid relative turnover. The development study found eight
events on eight dates, with four events in 2013–2016. Mean net was **−0.53% at 1×
and −0.75% at 2×** through the close. The later four events averaged −3.98% and −4.17%.
The sample and return gates in the [preregistration](HYPOTHESIS.md) failed and the
portfolio and validation phases were not started.

Run `20261116T061016Z_gpt_new_listing_drift_31c2ffd9`, 2003-09-10 to 2016-12-30,
used clean commit `fdfd9b07`, preregistration `771f95f` and build `447e58e098`.
It was one trial in the new family. All eight entries were on time and all eight
run-time lookahead replays passed.

| Close outcome | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | −0.53% | −0.75% |
| 95% day-clustered interval | −4.92% to +3.20% | −5.12% to +2.92% |
| Summed event P&L | −$86 | −$122 |
| Daily event P&L t-statistic | −0.26 | −0.37 |
| Worst end-of-day drawdown of summed events | −$327 | −$345 |

The gross mean was −0.23%. Dollar results are computed from saved event returns and
order notionals summed across 3,352 sessions, without portfolio or participation
constraints. Observed session count is a listing-age proxy. A verified listing-event
source would help establish eligible candidates and separate relistings from true
IPOs. The estimate is too imprecise for a general claim about the IPO aftermarket.

| Year with events | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2008 | 1 | +0.58% | +0.38% | +$12 | +$8 |
| 2009 | 1 | +4.52% | +4.43% | +$90 | +$88 |
| 2010 | 1 | +7.04% | +6.45% | +$139 | +$128 |
| 2011 | 1 | −0.45% | −0.64% | −$9 | −$13 |
| 2013 | 1 | −12.79% | −13.12% | −$256 | −$262 |
| 2014 | 1 | +1.83% | +1.76% | +$36 | +$35 |
| 2015 | 1 | +0.62% | +0.43% | +$12 | +$8 |
| 2016 | 1 | −5.59% | −5.73% | −$111 | −$114 |
