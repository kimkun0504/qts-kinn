# Search on recent years

**Verdict: no rule found. 2,171 combinations of conditions were measured on 2018 to 2022 and
none comes near 3% a trade for a long-only account; none even qualifies as a near miss (1.5%).
The large, repeatable intraday moves in these years are downward, in small stocks that have
already run up, and only a short seller collects them. The 2023 check period was not opened,
because nothing was shortlisted.**

Plan and the rule for selection: [HYPOTHESIS.md](HYPOTHESIS.md) (decision 0019). Code:
`research/claude/recent_features.py`, `recent_base.py`, `recent_premarket.py`,
`recent_search.py`. Data: 6.05 million stock-days, 1,463 full sessions, 2018-01-02 to
2023-11-08 (2023 built but not read by any search). Net is after costs at twice the modelled
spread. No holdout data.

## What was measured

| Family | Cells | Long candidates | Best long cell with 300+ trades (net at 2×) |
|---|---|---|---|
| 1. Gap, 8-K news, premarket volume, size (09:35) | 198 | 0 | −0.03% |
| 2. Opening drive, relative volume, trade size, size (10:00) | 215 | 0 | +0.21% |
| 3. Move so far, relative volume, size (11:00, 13:00, 15:00) | 216 | 0 | −0.06% |
| 4. Day two after a 10% or 20% session | 140 | 0 | +1.67% (2020 only; four of five years negative or flat) |
| 5. 8-K item type, gap direction, size | 292 | 0 | −0.43% |
| 6. VWAP and range position among active stocks (11:00) | 40 | 0 | −1.38% |
| 7. First 20 sessions after listing | 30 | 0 | −0.42% |
| 8. Trade-size signature (10:00) | 48 | 0 | −0.92% |
| 10. Resting bids 5% to 30% below the market | 276 | 0 | +3.09% (2020 only; negative in 2018, 2021, 2022) |
| 9. Premarket: buy at 07:00, 08:00 or 09:00; sell at the open, 09:35, 10:00 or the close | 716 | 0 | −0.05% |
| **Total** | **2,171** | **0** | |

Selection needed 300 trades, 3% net at 2×, a t-statistic of 4 on daily means and a positive
result in every year 2018 to 2022.

## What the search shows

- **A market buy held to the close earns under 1% before costs in almost every state.** News
  type, gap size, relative volume, trade size, VWAP position, age and size move the average by
  tenths of a percent, not by whole percents.
- **Deep resting bids** are the one long structure with returns of 2% to 3% a fill, and they
  owe it to 2020. Every deep-bid cell is weaker or negative in 2022. This is the rebound again.
- **The big moves are down, and they are steady.** Stocks up 50% or more before the open on
  heavy premarket volume and no filing lose 6% to 7% from 08:00 or 09:00 to the close (508 to
  613 cases, t about −7, negative in every year). Stocks up 20% to 50% lose about 4%. Stocks
  that gapped up 50% lose 6.9% from 09:35. Stocks already down 10% to 20% at 11:00 on normal
  volume lose another 1.7%.
- **Those are short trades.** After costs at 2× the best of them nets about 3% a trade to a
  short seller, and less each year: the fade of the largest premarket runners earned about 8%
  before costs in 2018 and 1% or less in 2022. Shares of such stocks are often unavailable to
  borrow or cost a great deal, a short sale cannot hit the bid once a stock is down 10%, and a
  short can lose more than its size. None of that is in the figures.

## What it means for the target

Within one session, long only, in these data, 3% a trade is not there to be found by
conditioning on price, volume, trade size, company size, news type or time of day. The
ways left to reach it change the brief: sell short (the engine and the cost model would need
borrow and locate), hold longer than a day, or accept a smaller edge on many trades (the
opening range breakout in `strategies/intraday_momentum`).

Not tested for lack of data: news with a time of day or with text, short interest and borrow
cost, halts, options.

## Timed news and short interest, 2026-11-16 (addenda of 11:20 and 12:05 ET)

**Verdict: timed news adds no long candidate either. 518 more cells (2,689 in all), none
shortlisted, no near miss. The one effect above 3% a trade is still a short sale: fading
stocks that are up 50% or more before the open, and short interest sharpens it.** The 2023
check remains unopened.

Data from the owner's download (`tools/owner/download_news.py`): 540,295 articles, but only
287 before 2021, so the news search covers 2021 and 2022. Company press releases come from one
wire, GlobeNewswire (105,354); the rest is commentary. Benzinga's feed is not in the plan,
short volume returned nothing for these years, and sentiment labels start in July 2024, inside
the sealed period. Short interest: 2.48 million rows, used from 14 days after settlement.
Code: `research/claude/recent_news.py`, `recent_short_interest.py`.

| Family 11 | Cells | Long candidates | Best long cell with 150+ trades (net at 2×) |
|---|---|---|---|
| a. Release before the open; buy 09:35, sell at the close (headline group × gap × size) | 132 | 0 | +0.10% |
| a. Buy at the premarket checkpoint after the release; sell at the open, 10:00 or the close | 141 | 0 | −1.82% |
| b. Release during the session; buy 1 or 5 minutes after; sell after 15 or 60 minutes or at the close | 201 | 0 | −0.92% |
| c. Short interest and days to cover on the premarket runners | 44 | 0 | −1.75% |

- **After a release during the session nothing happens that a buyer can use.** In almost every
  case the price one minute after the stamped time is within 1% of the price before it, and
  the return from there is zero to the second decimal. Either most releases do not move the
  stock, or the stamp is later than the moment the market saw the news; this archive cannot
  tell the two apart.
- **Stocks bought before the open after a release lose** 0.2% to 1.7% before costs, whatever
  the headline group. Results, trial news, contracts and offerings all fade from the premarket
  price.
- **Short interest does not reveal squeezes that continue.** Among stocks up 20% or more
  before the open on heavy volume, the best group for a buyer (over 15% of shares short, more
  than 5 days to cover) earned +0.4% before costs on 128 cases.
- **It does sharpen the fade.** Stocks up 50% or more before the open with under 5% of shares
  short and under 2 days to cover lost 9.8% from 08:00 or 09:00 to the close (208 and 254
  cases, 2018 to 2022; 7% to 9% in 2021 and 2022). To a short seller that is about 5% a trade
  after costs at 2×. Borrow availability and cost, the 10% short-sale rule and the risk of an
  unlimited loss are not in that figure, and these are the stocks where all three bite.

Not available from this subscription: Benzinga's timed headlines, PR Newswire and Business
Wire releases, stock-loan availability and fees.
