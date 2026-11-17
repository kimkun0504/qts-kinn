# News hours: news is priced within minutes; only results keep going, and not by enough

**Verdict: closed.** 360 cells on 2010 to 2017 (228 with 150 trades or more), none meets the
bar, so no test was run and the holdout is untouched. 360 trials.

Plan, events and bars: [HYPOTHESIS.md](HYPOTHESIS.md). 726,077 entries from 776,000 8-K
events, 2005 to October 2023, timed by the SEC's acceptance of the filing and read on minute
bars. Code: `research/claude/news_hours.py`.

## What a stock does after news (2010 to 2017, every kind and size, before costs)

| When the filing came | Move by the time of buying | Events | To that day's close | Five sessions on |
|---|---|---|---|---|
| Before the session; read at 09:35 against yesterday's close | down 5% or more | 13,423 | −0.40% | −0.73% |
| | down 2% to 5% | 19,595 | −0.19% | −0.06% |
| | within 2% | 181,070 | +0.01% | +0.14% |
| | up 2% to 5% | 21,033 | +0.16% | +0.25% |
| | up 5% or more | 13,765 | +0.24% | +0.63% |
| During the session; five minutes after, against yesterday's close | down 5% or more | 2,002 | −0.25% | −1.28% |
| | within 2% | 38,262 | +0.02% | +0.14% |
| | up 5% or more | 2,355 | +0.24% | +0.40% |
| During the session; five minutes after, against the last trade before the filing | within 2% | 52,413 | +0.03% | +0.13% |
| | moved 2% or more, either way | 441 | | |

- **The owner's instinct is right about the direction and wrong about the size.** A stock up
  on news keeps rising and a stock down on news keeps falling, in every row. But what is
  left after the first minutes is a quarter of a percent by the close and half a percent
  over a week. Buying costs 0.2% to 1.3% in these stocks. The move is made before anyone
  reading the filing can act.
- **The filing itself almost never moves the price.** In 99% of filings made during the
  session the stock is within 2% five minutes later. The news was already out (the press
  release comes first) or it was not news.

## By kind of news: only results continue

Bought at 09:35 after a filing before the session, stock up 5% or more, held five sessions,
2010 to 2017, after costs.

| Kind | $50M–$300M | $300M–$2B | $2B and over |
|---|---|---|---|
| Results | +0.86% (1,852; 7 years of 8) | +0.58% (5,160; t 4.5; 7 of 8) | +0.01% (3,474) |
| Agreements | −1.04% (396) | −0.24% (489) | −0.07% (226) |
| Announcements | −2.64% (657; 0 of 8) | −0.95% (787) | −0.23% (354) |
| Other | −2.53% (154) | | |

- **Results drift; nothing else does.** This is the earnings drift again, found a third way.
  At a 5% rise it is 0.6% to 0.9% a trade, under the 1% bar; the strategy that passed takes
  only the 15% rises on heavy volume in small companies, where it is 4% to 5%.
- **A small company up 5% on an announcement or an agreement gives it back:** about 1% by
  the close and 1.5% over the week before costs. That is a short sale in the stocks hardest
  to borrow, and half the size that would cover its costs.
- **Bought to the same day's close, no cell makes money after costs.** The best is +0.11%.

## What was not found

No cell reached 1% a trade after costs with a weekly t of 3 and six years of eight. The
nearest by t is results up 5% before the session in $300M–$2B companies (0.58%, t 4.5). The
largest mean is a 2% to 5% fall on results in small companies bought during the session
(1.46%, 302 trades, three years of eight, t 0). Neither goes forward.

## Limits

- The acceptance time is when the filing became public on EDGAR. A press release before it
  is not timed here, so "the first minute after the news" cannot be measured with this data;
  Benzinga's timed headlines would be needed, and the size of what is left after five
  minutes says the first minute is where it is.
- Entries pay the modelled spread, not measured quotes.
- Only purchases were counted against the bar. The falls after bad news (0.7% to 1.3% over
  five sessions) are in the tables and were not pursued (`short_search` closed the same day).

## Reproduce

```
cd research/claude
uv run python news_hours.py events
uv run python news_hours.py collect 2005 2023
uv run python news_hours.py search
```
