# Overnight offerings: the open after a deal is about the right price

**Verdict: closed.** 30 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 30 trials. The holdout is untouched.

A prospectus supplement (424B5) accepted between 16:00 and 09:15, in a listed company of $50M
or more that files six or fewer a year and has no results due: 14,210 events, 2003 to October
2023. Four in five opened unchanged (routine shelf takedowns); 2,230 opened 3% to 10% down and
681 opened 10% or more down (median −14.7%). Code: `research/claude/overnight_offering.py`.

| 2010–2017, after costs | Trades | Out at the close | 5 sessions | 15 sessions |
|---|---|---|---|---|
| Bought, opened 3–10% down, $50M–$300M | 262 | −1.05% | −0.96% | −0.27% |
| Bought, opened 3–10% down, $300M–$2B | 540 | −0.62% | −0.41% | −0.12% |
| Bought, opened 3–10% down, $2B+ | 199 | −0.30% | −0.30% | +0.72% |
| Bought, opened 10%+ down, $50M–$300M | 168 | −1.07% | −1.25% | −1.79% |
| Bought, opened 10%+ down, $300M–$2B | 58 | −1.74% | −1.33% | −0.81% |
| Sold short, opened 10%+ down, $50M–$300M | 168 | −0.15% | −0.17% | |
| Sold short, opened 10%+ down, $300M–$2B | 58 | +1.10% (t 1.47) | +0.48% | |

The other short cells are between −0.4% and +0.1%.

- **The supply does not bounce.** A stock that opens down after a deal keeps drifting lower
  by about 1% in small and mid companies, and there is nothing to buy.
- **Nor does it collapse.** Selling it short at the open made nothing after costs, before
  counting how hard such stocks are to borrow.

## Reproduce

```
cd research/claude
uv run python night_bids.py filings
uv run python overnight_offering.py events
uv run python overnight_offering.py search
```
