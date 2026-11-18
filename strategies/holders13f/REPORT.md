# New institutional holders: no signal

**Verdict: closed.** 8 cells on the 2013 to 2017 signals, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 8 trials. The holdout is untouched.

Sharadar's 13F counts (SF3A, from June 2013; rows after June 2023 left out): for each quarter,
the 20 companies of $50M to $300M (or $300M to $2B) whose number of 13F holders rose most,
bought at the first open 60 days after the quarter and held 20 or 60 sessions. Code:
`research/claude/holders13f.py`.

| 2013–2017, 18 quarters, 360 trades a cell | Over the average stock, 20 sessions | 60 sessions |
|---|---|---|
| Most new holders, $50M–$300M | −0.73% (t −0.71) | −0.80% (t −0.82) |
| Most new holders, $300M–$2B | −0.04% (t −0.04) | +1.80% (t 0.99) |
| Largest rise as a share, $50M–$300M | +0.31% (t 0.28) | −0.05% (t −0.02) |
| Largest rise as a share, $300M–$2B | −1.38% (t −1.36) | −0.15% (t −0.06) |

By the time the reports are public, the buying they show is over.

## Reproduce

```
cd research/claude
uv run python holders13f.py table      # needs sf3a.parquet in the research folder (see HYPOTHESIS.md)
uv run python holders13f.py search
```
