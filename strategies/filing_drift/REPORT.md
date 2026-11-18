# Filing drift: the earnings rule does not carry over to the 10-Q

**Verdict: closed.** 3 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 3 trials. The holdout is untouched.

Rule A50's test (a two-session rise of 15% or more on five times normal dollar volume,
$50M to $300M) on the session after a 10-Q or 10-K, for companies with no results 8-K in the
ten sessions before: the companies whose quarter first becomes public in the filing itself.
Code: `research/claude/filing_drift.py`.

| 2010–2017, after costs | Trades | A trade | Median | Weekly t | Years positive |
|---|---|---|---|---|---|
| Q50 (A50's thresholds) | 99 | −1.80% | −0.70% | −0.93 | 3 of 8 |
| A rise of 10% or more | 143 | −1.18% | −0.59% | −1.27 | 3 of 8 |
| Q50's thresholds, $300M–$2B | 73 | +1.09% | +0.26% | 0.57 | 6 of 8 |

The drift A50 trades needs a results press release. A jump on the filing alone, in a company
that does not issue one, is given back.

## Reproduce

```
cd research/claude
uv run python filing_drift.py events
uv run python filing_drift.py search
```
