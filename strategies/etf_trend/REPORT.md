# ETF trend: it sat out 2008 and earned little

**Verdict: closed.** Two fixed rules, no search, March 2007 to September 2023. Neither meets
the bar set in [HYPOTHESIS.md](HYPOTHESIS.md). 2 trials. The holdout is untouched.

Nine funds (SPY, IWM, EFA, EEM, TLT, IEF, GLD, DBC, VNQ), cash in SHY, decided at each month
end and traded at the next close, 5 basis points a side. Code: `research/claude/etf_trend.py`.

| | A year | Sharpe over cash | Worst drawdown | 2008 | 2022 | Worst year |
|---|---|---|---|---|---|---|
| **T1: each fund held while above its ten-month average** | 4.1% | 0.37 | 13.1% | +0.1% | −9.1% | 2022 |
| **T2: the strongest three over twelve months** | 5.0% | 0.31 | 25.8% | −1.0% | −7.9% | −10.9% (2011) |
| All nine held all the time | 5.5% | 0.34 | 38.0% | −18.7% | −14.1% | 2008 |
| 60% SPY, 40% IEF | 7.3% | 0.53 | 31.4% | −16.7% | −16.4% | 2008 |

- **T1 did the one thing it is for.** It was flat in 2008 while the same funds held throughout
  lost 19%, and its worst drawdown was 13% against 38%.
- **It paid for that everywhere else.** 4.1% a year with a Sharpe ratio of 0.37, in both
  halves (0.35 and 0.41; the bar was 0.5). It lost 9% in 2022, when stocks and bonds fell
  together and there was nothing rising to hold. Simply holding the funds made more.
- **T2 is worse:** a 26% drawdown and a Sharpe ratio of 0.31.

**Beside the earnings book** (the idle $13,000 in the sleeve, by month): the correlation is
low (0.22 for T1), and the two together make $5,533 a year against $4,974 with a slightly
higher Sharpe ratio (1.23 against 1.17) and a slightly lower worst year ($1,763 against
$1,929). That is about $560 a year from $13,000, which Treasury bills at 4% would also pay
with no drawdown.

**What it says.** Trend following on funds is protection against a long decline, bought with
most of the return. It is not a second strategy by the owner's targets, and for the idle
money it is no better than bills at present rates. If the aim were only to be out of stocks
in a long bear market, T1 does that; it should be chosen for that reason, not for return.

## Reproduce

```
cd research/claude
uv run python etf_trend.py funds
uv run python etf_trend.py measure
```
