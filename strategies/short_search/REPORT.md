# Short search: nothing passes

**Verdict: closed for now.** 24 cells on 2010 to 2017 and 6 test runs (30 trials). Three
cells met the search bar and all three failed their tests. The holdout is untouched.

Plan, universe and bars: [HYPOTHESIS.md](HYPOTHESIS.md). Sell short at the open after the
signal, buy back at the close 5 or 15 sessions after it. Common stock of $50M or more,
$3 or more, $1M or more traded a day. Costs: the auction allowance and commission both ways
and a borrow fee of 10% a year. Code: `research/claude/short_search.py`.

## The search, 2010 to 2017

Mean a trade to the short seller after all costs. Sizes: $50M–$300M, $300M–$2B, $2B and over.

| Event | Hold | Small | Mid | Large |
|---|---|---|---|---|
| A fall on earnings (−15% in two days, 5× volume) | 5 | +0.67% (271) | −0.35% (1,148) | −0.67% (479) |
| | 15 | −0.08% | −1.42% | −1.00% |
| An earnings jump given back by the close | 5 | −0.21% (78) | −0.92% (705) | −0.39% (240) |
| | 15 | −3.25% | −2.29% | −2.23% |
| A 30% jump with no filing | 5 | +4.73% (115) | −0.45% (110) | +2.24% (22) |
| | 15 | +11.71% | −0.16% | +1.07% |
| Up 100% in 20 sessions, at a yearly high | 5 | **+3.75% (422)** | **+2.51% (479)** | +0.04% (120) |
| | 15 | **+4.11%** | +2.14% | −1.50% |

Bold cells met the bar (150 trades, 2% after costs, weekly t of 3, six years of eight,
above the average stock).

- **Falls on earnings do not continue.** A stock down 15% on its report is, if anything, a
  little higher three weeks later. Selling it short loses.
- **A given-back earnings jump is not a short.** From the next open these stocks rise 1.5% to
  2.4% over 15 sessions. The fall the buyer's study saw (`swing_search`, family 23) is taken
  entirely on the day of the jump.
- **A 30% jump with no filing in a small company** fell 12% in three weeks, seven years of
  eight, but on 115 trades, under the 150 the plan required, and one trade lost 111%. Noted,
  not taken forward.

## The tests: all three fail

Pass was 1% after costs, weekly t of 2.5, four years of five positive, in both periods.

| Cell | 2005–2009 | 2018–2022 | Worst trade |
|---|---|---|---|
| Run-up, small, 5 sessions | +0.77%, t 1.36, 3 of 5 | +0.11%, t 1.92, 2 of 5 | −390% |
| Run-up, small, 15 sessions | +2.40%, t 1.60, 4 of 5 | +2.88%, t 1.10, 3 of 5 | −355% |
| Run-up, mid, 5 sessions | −1.21%, t 0.77, 3 of 5 | +1.05%, t 3.48, 3 of 5 | −332% |

Selling short a stock that has doubled in a month made money on average in the small
companies (2.4% and 2.9% a trade over 15 sessions), but not steadily: 2009 lost 4%, 2018 lost
13%, and single trades lost three to four times the position, because a stock that has
doubled can double again. An average of 3% with losses of 350% is not a strategy for a
$20,000 account.

## What this says

- For holds of one to three weeks, in stocks large enough that borrowing them is plausible,
  the events that looked like shorts from the buyer's side are not. Bad news does not keep
  falling, and failed jumps finish failing the same day.
- The falls that are real are fast and in the stocks hardest to borrow: the fade of a stock
  up 50% before the open (`recent_search`: about 5% a trade to a short seller between 08:00
  and the close, before borrow), and the no-news spike in a small company above. Both need
  stock-loan data (which shares can be borrowed, at what fee) before another hour is spent
  on them, and neither would be sized large on a small account.
- Not tested: shorts inside the day; pairs (short one stock against another); shorts of
  companies under $50M or stocks under $3.

## Reproduce

```
cd research/claude
uv run python short_search.py search
uv run python short_search.py test run_up small 15
```
