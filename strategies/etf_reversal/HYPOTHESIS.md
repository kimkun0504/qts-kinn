# Hypothesis: buying short falls in index funds

Written 2026-11-17 00:04 ET, before any return is measured. Why now: the earnings rule that
works cannot carry much money (it stops growing at about $20,000 to $25,000 a year, because
its stocks are small), and its version in larger companies no longer exists. Index funds are
the other end: any size trades at almost no cost. The question is whether a plain swing rule
on them earns anything worth having. This is a new family, `etf_swing`, with its own holdout,
which nothing has touched.

## Why it might work

Broad index funds have tended to bounce after a few down days: sellers who must sell are met
by buyers who can wait. The effect was strong from the late 1990s to the early 2010s and is
in every trading book.

## Why it might not

It is in every trading book. The edge a trade is small (well under 1%), it is known to have
faded, and the fall that never bounces (2008, 2020, 2022) is where the losses are. A rule
that sits in cash most of the time and makes a few percent a year is the bank account the
owner does not want.

## Data

Daily bars of 14 funds from `store.daily`, 2003-09-10 on: SPY, QQQ (joined to its earlier
symbol QQQQ), IWM, DIA, MDY, and the nine sector funds XLB, XLE, XLF, XLI, XLK, XLP, XLU,
XLV, XLY. The bars are not adjusted: an overnight move of more than 12% in one of these funds
is taken to be a split or a special distribution and set to zero; ordinary dividends are left
in, which understates returns slightly.

## Trade

Signal at a close; buy at the next open; sell at the first close above the fund's 5-day
average of closes, or at the close of the 10th session. Cost 0.03% a side.

## Cells (8)

- **A new low close:** today's close is under every close of the previous N sessions,
  N = 5 or 10.
- **Falling closes:** the close is lower than the one before, 3 or 4 sessions running.
- Each with and without a trend filter: the close is above the fund's 200-day average.

## Test

Chosen on signals of 2004 to 2014, tested on 2015 to October 2023, all 14 funds pooled.

- **To be taken forward** a cell needs, where chosen, 0.5% or more a trade with a weekly
  t-statistic of 3 or more; and where tested, 0.4% or more a trade, at least 7 of 9 years
  positive, and a book ($20,000, at most four positions of $5,000, the largest fall first)
  whose worst year loses less than $600 (3% of the account) and which earns at least $1,000
  a year. The book matters more than the mean: the funds fall together, so the signals come
  on the same days.
- If a cell passes it is fixed here and left for this family's holdout. If none does, the
  family is closed: the idea is recorded as too thin to be worth the owner's capital.

8 trials.
