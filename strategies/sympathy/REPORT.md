# Sympathy: bad news spreads slowly to the peers, good news does not

**Verdict: closed (no long trade).** 8 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 8 trials. The holdout is untouched.

Trigger: a results 8-K after the close in a company of $300M or more that is down (or up) 15% or
more half an hour later. Peers: same industry, $300M or more, $1M a day, $5 or more, no results
of their own that night. A peer that opens the next session 2% or 3% beyond its close in the
same direction, bought at that open. Code: `research/claude/sympathy.py`.

| 2010–2017, after costs | Trades | Out at the close | Five sessions | Years positive (close) |
|---|---|---|---|---|
| After a collapse, peer opened 2%+ down | 388 | −1.01% | −1.48% | 2 of 8 |
| After a collapse, peer opened 3%+ down | 181 | −1.28% | −1.82% | 2 of 8 |
| After a jump, peer opened 2%+ up | 156 | −0.01% | +0.70% | 3 of 8 |
| After a jump, peer opened 3%+ up | 83 | −0.16% | +0.63% | 3 of 8 |

- **Peers dragged down by an industry collapse keep falling** through the session and the week,
  as the company itself does after hours. It is the same slow spread of bad news that makes the
  after-hours short work; here it would also be a short, which the owner cannot count on.
- **Good news does not spread that way.** The asymmetry is the classic one: bad news is slow
  where selling short is hard.

## Reproduce

```
cd research/claude
uv run python sympathy.py table
uv run python sympathy.py search
uv run python sympathy.py table_up
uv run python sympathy.py search_up
```
