# Report timing: lateness against the company's own calendar says nothing tradable

**Verdict: closed.** 6 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 6 trials. The holdout is untouched.

Expected session: the anniversary of the same company's report a year earlier (reaction
sessions from the SEC acceptance times). Code: `research/claude/report_timing.py`.

| 2010–2017, after costs | Trades | A trade | Median | Weekly t | Years positive |
|---|---|---|---|---|---|
| Late at E+2, sold short to the report, $300M–$2B | 9,962 | −0.11% | −0.29% | −1.41 | 5 of 8 |
| Late at E+2, $2B+ | 8,971 | −0.19% | −0.25% | −1.19 | 3 of 8 |
| Late at E+5, $300M–$2B | 3,918 | −0.32% | −0.31% | −0.62 | 4 of 8 |
| Late at E+5, $2B+ | 2,880 | −0.44% | −0.52% | −1.36 | 2 of 8 |
| Early by 7+ days, bought after the report, $50M–$300M | 1,734 | −0.79% | −0.93% | −0.48 | 3 of 8 |
| Early by 7+ days, $300M–$2B | 4,118 | +0.21% | −0.14% | 2.50 | 5 of 8 |

Many "late" companies have simply moved their calendar; the published effect, measured on
announced dates, does not show on filing dates here.

## Reproduce

```
cd research/claude
uv run python report_timing.py events
uv run python report_timing.py search
```
