# Before the report: a company's past reactions do not predict its next one

**Verdict: closed.** 18 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 18 trials. The holdout is untouched.

The owner asked for earlier entries; the earliest is before the report. 225,741 results
reports with their reaction session, 2005 to October 2023. Bought at the close five sessions
before; sold at the close before the report (the run-up alone) or at the close of the session
after it (through the report). Code: `research/claude/before_report.py`.

| 2010–2017, after costs | Trades | Run-up only | Through the report | Weekly t (through) | Worst (through) |
|---|---|---|---|---|---|
| Last report rose 10%+, $50M–$300M | 1,335 | −0.50% | −0.98% | −1.13 | −86% |
| Last report rose 10%+, $300M–$2B | 3,965 | −0.24% | +0.11% | 0.21 | −72% |
| Last report rose 10%+, $2B+ | 1,816 | +0.14% | −0.12% | 0.93 | −54% |
| Last two reports rose 5%+, $50M–$300M | 562 | −0.45% | −0.92% | −1.16 | −82% |
| Last two reports rose 5%+, $300M–$2B | 2,294 | +0.04% | +0.29% | 0.57 | −61% |
| Last two reports rose 5%+, $2B+ | 1,372 | +0.10% | +0.17% | 0.29 | −48% |
| Every report, $50M–$300M | 15,542 | −0.53% | −0.92% | −0.59 | −86% |
| Every report, $300M–$2B | 40,955 | −0.30% | −0.27% | −0.22 | −79% |
| Every report, $2B+ | 37,177 | +0.05% | +0.07% | −0.17 | −87% |

- **The record does not carry over.** After a report that jumped 10% or more, the next
  report's reaction averaged about zero, the same as any report. The earnings rule cannot be
  entered a quarter early.
- **There is no run-up to buy.** The five sessions before a report gained under 0.2% before
  costs in every size.
- **Holding small companies through results lost money** (−0.9% a trade after costs), with
  single losses of 50% to 86%.

The trade used the actual report date five sessions ahead, which favours it; it failed
anyway, so the check with predicted dates was not needed.

## Reproduce

```
cd research/claude
uv run python before_report.py table
uv run python before_report.py search
```
