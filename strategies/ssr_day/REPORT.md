# SSR day: the circuit breaker does not lift the next session

**Verdict: closed.** 4 cells on 2011 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 4 trials. The holdout is untouched.

Stocks of $300M or more, $1M a day, $5 or more, no results near: 101,349 sessions with a low
10% or more under the previous close (the short-sale rule trips from 2011) and 99,456 near
misses (8% to 10%), 2005 to October 2023. Bought at that close, sold at the next. Code:
`research/claude/ssr_day.py`.

| After costs, the next session | 2005–2010 (no rule) | 2011–2017 (rule) | Near misses, 2011–2017 |
|---|---|---|---|
| $300M–$2B, closed less than 10% down | −0.25% | −0.43% (t −2.61) | −0.21% |
| $300M–$2B, closed 10%+ down | +1.11% | +0.07% | — |
| $2B+, closed less than 10% down | +0.02% | −0.35% (t −1.12) | −0.28% |
| $2B+, closed 10%+ down | +7.93% (2008–09) | +0.29% (t 0.94) | — |

Restricting short sales for a session does not show in the price: stocks that tripped the
rule did a little worse than those that stopped just short of it.

## Reproduce

```
cd research/claude
uv run python night_bids.py filings
uv run python ssr_day.py table
uv run python ssr_day.py search
```
