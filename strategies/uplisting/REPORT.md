# Uplisting: small companies that move up trail other stocks

**Verdict: closed.** 4 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 4 trials. The holdout is untouched.

Moves from OTC or NYSE American to Nasdaq or the NYSE (Sharadar exchange changes), $50M to
$2B, $250,000 traded on the first session: 555 events, 2005 to October 2023. Bought at the open
after the first session on the new market. Code: `research/claude/uplisting.py`.

| 2010–2017, against the average stock | Trades | 20 sessions | 60 sessions |
|---|---|---|---|
| $50M–$300M | 115 | −2.06% (t −1.36) | −5.42% (t −1.88) |
| $300M–$2B | 69 | +0.59% (t 0.21) | −0.97% (t −0.22) |

A move up is often paired with a share sale and comes after a run; the new buyers do not show.

## Reproduce

```
cd research/claude
uv run python uplisting.py table     # needs exchanges.parquet (Sharadar exchange changes before the seal)
uv run python uplisting.py search
```
