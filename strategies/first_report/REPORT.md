# First report: a sign on a handful of trades, nothing steady

**Verdict: closed.** 8 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 8 trials. The holdout is untouched.

A50's test on results of newly listed stocks (blank-check companies left out). Code:
`research/claude/first_report.py`.

| 2010–2017, after costs | Trades | A trade | Median | Weekly t | Years positive |
|---|---|---|---|---|---|
| First report, 15% on 5×, $50M–$300M | 3 | −9.30% | | | |
| First report, 15% on 5×, $300M–$2B | 12 | +15.99% | +12.28% | 2.72 | 6 of 6 |
| First report, 10% on 3×, $50M–$300M | 6 | −9.09% | | | |
| First report, 10% on 3×, $300M–$2B | 41 | +4.68% | +1.86% | 1.94 | 7 of 8 |
| First 400 sessions, 15% on 5×, $50M–$300M | 62 | +1.04% | −0.69% | 0.33 | 4 of 8 |
| First 400 sessions, 15% on 5×, $300M–$2B | 148 | +1.67% | −0.03% | 1.75 | 6 of 8 |
| First 400 sessions, 10% on 3×, $50M–$300M | 116 | +2.23% | +1.48% | 0.97 | 5 of 8 |
| First 400 sessions, 10% on 3×, $300M–$2B | 351 | +0.80% | −0.08% | 1.70 | 4 of 8 |

A strong first report in a mid-sized new listing did well in 2010–2017, on 12 to 41 trades; it
is too rare to be a rule, and the first year of reports as a whole does not drift.

## Reproduce

```
cd research/claude
uv run python first_report.py spacs
uv run python first_report.py firsts
uv run python first_report.py search
uv run python first_report.py search_year
```
