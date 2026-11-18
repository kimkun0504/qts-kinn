# Late filer: when the overdue report arrives, the stock keeps falling

**Verdict: closed (no long trade; a warning).** 8 cells on 2010 to 2017, none meets the bar
set in [HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 8 trials. The holdout is untouched.

A notice of late filing (NT 10-Q or NT 10-K) followed within 20 days by the report, in listed
common stock of $50M or more with no results 8-K in the ten sessions before: 1,806 events,
2003 to October 2023. Code: `research/claude/late_filer.py`.

| 2010–2017, after costs, 15 sessions | Trades | Bought at once | Bought after a session | Years positive (after) |
|---|---|---|---|---|
| Every event, $50M–$300M | 174 | −3.04% | −3.09% (t −2.11) | 1 of 8 |
| Every event, $300M+ | 179 | −0.25% | −0.17% | 3 of 8 |
| Fell 10%+ since the notice, $50M–$300M | 28 | −7.09% | −8.35% (t −2.57) | 0 of 8 |
| Fell 10%+ since the notice, $300M+ | 16 | −4.55% | −5.97% | 1 of 7 |

- **There is no relief rally.** The report that ends a late filing is usually the bad news the
  notice hinted at, and small companies keep falling for weeks after it.
- **Use:** a holding of a small company that files a late notice is not one to keep through
  the report; and no new position should be opened in one until weeks after it.

## Reproduce

```
cd research/claude
uv run python late_filer.py events
uv run python late_filer.py search search
```
