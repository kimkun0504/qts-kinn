# Dividend signal: no drift worth trading after a dividend is started or raised

**Verdict: closed.** 8 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 8 trials. The holdout is untouched.

Sharadar's dividend history (dated at the ex-date): an initiation (no dividend in two years,
two years of prices) or a raise of 1.25 to 3 times (60 to 120 days after the last one, no
split between), in companies of $50M to $2B. Bought at the ex-date's open. Code:
`research/claude/dividend_signal.py`.

| 2010–2017 | Trades | Over the average stock, 20 sessions | 60 sessions |
|---|---|---|---|
| Initiation, $50M–$300M | 107 | −0.45% (t −0.38) | +2.07% (t 0.88) |
| Initiation, $300M–$2B | 266 | +1.73% (t 0.92) | +1.46% (t 0.55) |
| Raise, $50M–$300M | 169 | −0.11% (t 0.61) | +1.79% (t 1.75) |
| Raise, $300M–$2B | 636 | +0.23% (t 1.51) | +1.44% (t 1.82) |

After costs the trades made 1% to 5% because the market rose; against other stocks the
dividend adds about a point over three months, too unsteady to trade.

## Reproduce

```
cd research/claude
uv run python dividend_signal.py table
uv run python dividend_signal.py search
```
