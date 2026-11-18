# Net-nets: most trail, a few multiply, nothing steady

**Verdict: closed.** 8 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 8 trials. The holdout is untouched.

Quarterly reports (Sharadar SF1, filed before the seal) of listed common stock of $30M or more
whose market value was under current assets less total liabilities: 1,962 events, 2005 to
October 2023, 832 of them companies located in China or Hong Kong. Bought at the open after
the first session on or after the filing, held 120 or 250 sessions (a stock that stopped
trading counted at its last close). Code: `research/claude/net_net.py`.

| 2010–2017, against the average stock of $30M–$300M | Trades | Mean | Median | t |
|---|---|---|---|---|
| Under 1×, 120 sessions, every company | 229 | +0.36% | −9.3% | 0.01 |
| Under 1×, 120 sessions, China and Hong Kong left out | 141 | +4.90% | −6.1% | 0.46 |
| Under 1×, 250 sessions, every company | 229 | −2.05% | −19.9% | −0.76 |
| Under 1×, 250 sessions, China and Hong Kong left out | 141 | +1.24% | −17.0% | −0.50 |
| Under ⅔, 120 sessions, every company | 106 | −1.38% | −10.1% | 0.18 |
| Under ⅔, 250 sessions, every company | 106 | +9.97% | −18.2% | 1.06 |
| Under ⅔, 250 sessions, China and Hong Kong left out | 48 | +21.57% | −22.7% | 0.91 |

The typical net-net trails other small companies; the average is carried by a few that
multiply. A book of them would be a lottery, not a strategy.

## Reproduce

```
cd research/claude
uv run python net_net.py table      # needs ncav.parquet (current assets and liabilities from raw SF1, see HYPOTHESIS.md)
uv run python net_net.py search
```
