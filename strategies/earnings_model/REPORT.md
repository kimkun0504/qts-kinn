# Earnings model: it finds A50's neighbours, and they do not hold up

**Verdict: closed.** One model, fixed before it was fitted, two cells; both fail the test set
in [HYPOTHESIS.md](HYPOTHESIS.md). 2 trials. The holdout is untouched.

Every session after a results 8-K in listed common stock of $50M to $2B, 2005 to October 2023
(149,263 events, 1,560 of them A50 signals). LightGBM on 25 features known at the close
(returns over 1 to 250 sessions, volume against normal, gap, close in the range, volatility,
value and profit facts, size, and the first and last half hour of the two report sessions),
fitted on 2010–2017, applied unchanged elsewhere. Code: `research/claude/earnings_model.py`.

| After costs, a trade | 2010–2017 (out of fold) | 2005–2009 | 2018–2022 | 2023 |
|---|---|---|---|---|
| Every event | +0.08% | (data error, see below) | −0.08% | −2.78% |
| A50 | +3.26% | +4.49% | +4.13% | +5.95% |
| Model's top 10% | +0.99% (t 3.87) | −0.69% (t 2.63) | +1.52% (t 0.83) | −2.76% |
| Model's top 5% | +1.72% (t 4.03) | −1.18% (t 2.03) | +2.08% (t 0.36) | −2.91% |

- The model's picks are 95% events A50 does not take, and those are not steady: 2008 −5%,
  2019 −2% to −3.5%, 2020 +6% to +8%, 2023 −3%.
- It leans on the run before the report and on value and size; the new half-hour features
  are not among its ten most used.
- A fixed rule found by hand (A50) beats a model given four times the information.

**Data error.** ASEI's open on 2007-08-09 is $0.01 in the panel (close $63.46): any trade
priced at that open is wrong by a factor of thousands. The panel has 18 opens under a fifth
of the previous close on sessions that closed within a fifth of it (4 in stocks of $50M and
$250,000 a day). Studies that price at the open should drop them; A50's trades do not include
any.

## Reproduce

```
cd research/claude
uv run python intraday_shape.py collect 2005 2023
uv run python earnings_model.py table
uv run --with lightgbm python earnings_model.py fit
```
