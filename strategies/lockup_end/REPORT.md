# Lockup end: priced in advance

**Verdict: closed.** 9 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 9 trials. The holdout is untouched.

IPOs from 2005 (a listed domestic common stock whose company filed an S-1 in the year before
its first session; no blank-check companies or spin-offs), 180 days on: 2,158 lockup ends,
2005 to October 2023. Code: `research/claude/lockup_end.py`.

| 2010–2017, after costs | Trades | A trade | Weekly t | Years positive |
|---|---|---|---|---|
| Short from 6 sessions before to the session after, $50M–$300M | 196 | −1.37% | −1.27 | 3 of 8 |
| … $300M–$2B | 513 | +0.71% | 0.85 | 6 of 8 |
| … $2B+ | 160 | +0.61% | 0.70 | 4 of 8 |
| Bought 2 sessions after, held 10, $50M–$300M | 196 | −2.16% | −1.38 | 2 of 8 |
| … $300M–$2B | 511 | −0.63% | −0.56 | 2 of 8 |
| … $2B+ | 160 | −0.75% | −1.08 | 3 of 8 |
| Bought 2 sessions after, held 20, $50M–$300M | 196 | −3.20% | −2.04 | 2 of 8 |
| … $300M–$2B | 510 | −0.31% | 0.02 | 3 of 8 |
| … $2B+ | 160 | −0.50% | −0.83 | 3 of 8 |

The dip before the date is too small to sell short and there is no recovery after it; small
IPOs keep drifting down, which is the known weakness of new issues rather than the lockup.

## Reproduce

```
cd research/claude
uv run python lockup_end.py events
uv run python lockup_end.py search
```
