# Deal spread: the gap is there and it is too thin

**Verdict: closed.** 10 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run and the holdout is untouched. 10 trials.

1,279 first tender-offer statements (SC 14D9) and 4,343 first merger proxies (DEFM14A)
matched to stocks; 3,410 in the universe. Buy at the open after the filing; sell at the last
close the stock trades or after the hold. After costs, 2010 to 2017.

| | Trades | A trade | Weekly t | Held (sessions) | A year on the money | Worst trade | Worst 1% |
|---|---|---|---|---|---|---|---|
| Tender offer, to 20 sessions | 387 | +0.04% | −0.03 | 19.7 | 0.5% | −26% | −22% |
| Tender offer, to 60 | 387 | +1.05% | 1.70 | 34.5 | 7.6% | −35% | −30% |
| Tender offer, $300M and over, to 60 | 295 | +0.77% | 1.13 | 35.2 | 5.5% | −35% | −33% |
| Merger, pinned, to 60 | 529 | +0.29% | 0.30 | 37.4 | 1.9% | −95% | −43% |
| Merger, pinned, to 120 | 529 | +0.63% | 1.12 | 49.6 | 3.2% | −96% | −37% |
| Merger, pinned, $300M and over, to 120 | 435 | +0.91% | 1.76 | 52.6 | 4.3% | −96% | −38% |
| Merger, not pinned, to 120 (control) | 502 | +2.49% | 1.85 | 68.5 | 9.2% | −84% | −68% |

- **The trade works as described and pays too little.** 70% to 85% of the pinned positions
  end with the stock taken out, and six or seven years of eight are positive. But the average
  is 0.3% to 0.9% for a month and a half to two and a half months of holding: 2% to 4% a year
  on the money, about what cash earns, with the occasional loss of 35% to 95% when a deal
  fails.
- **Tender offers pay more (about 1% in seven weeks, 7.6% a year)** and still do not clear
  the bar: the weekly t is 1.7.
- By the time the merger proxy or the tender statement is filed, most of the gap has
  already closed. The gap is widest on the day the deal is announced, which this data does
  not time (that is an 8-K with a press release, not told apart from other 8-Ks here).
- As a use for the earnings book's idle money this is no better than Treasury bills, and it
  has a tail that bills do not have.

## Reproduce

```
cd research/claude
uv run python deal_spread.py table
uv run python deal_spread.py search
```
