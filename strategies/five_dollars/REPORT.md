# Five dollars: back over $5 is the end of a rally

**Verdict: closed.** 8 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 8 trials. The holdout is untouched.

A listed common stock that closed under $5 on each of the 60 sessions before and then closes
at $5 or more (raw price; no split near; no results in the two sessions), $50M or more and
$250,000 a day: 4,964 events, 2005 to October 2023. Code: `research/claude/five_dollars.py`.

| 2010–2017, against the average stock | Trades | 20 sessions | 60 sessions |
|---|---|---|---|
| First close over $5, $50M–$300M | 674 | −1.01% (t −0.98) | −3.10% (t −1.16) |
| First close over $5, $300M+ | 503 | +0.13% (t 0.38) | −1.63% (t −1.45) |
| Five closes over $5, $50M–$300M | 417 | −1.53% (t −1.83) | −2.30% (t −1.69) |
| Five closes over $5, $300M+ | 334 | −0.26% (t −0.22) | −1.19% (t −0.82) |

The money that can own a $5 stock does not arrive in a way the price shows; small companies
that make it back over $5 give some of the run back.

## Reproduce

```
cd research/claude
uv run python five_dollars.py table
uv run python five_dollars.py search
```
