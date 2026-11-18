# Dividend signal: a company that starts paying, or pays a quarter more

Written 2026-11-17 22:50 ET, before anything is measured. The one rule that works here trades a slow
belief in small companies after results. A company that starts paying a dividend, or raises
it by a quarter or more, tells the market the same kind of thing in a way it cannot take back:
its cash flow is durable. Published work (Michaely, Thaler and Womack; and others) finds the
price keeps rising for months after an initiation. Nothing here has used the dividend history.

## Data

Sharadar's corporate actions (ACTIONS, action "dividend", the amount a share, dated at the
ex-date), matched to the price panel by Sharadar ticker; read only for dates before
2023-11-09. The ex-date is announced weeks ahead, so a trade on it uses nothing not known.

## Events

- **Initiation:** a dividend on a company with at least two years of prices before it and no
  dividend in the 730 days before.
- **Raise:** a dividend 1.25 to 3 times the previous one, paid 60 to 120 days earlier (a
  regular dividend raised, not a special one).

Listed common stock, $250,000 a day, a close of $1 or more on the session before the ex-date.
Sizes: $50M to $300M; $300M to $2B.

## Trade

Bought at the ex-date's open (after the dividend is gone), sold at the close 20 or 60 sessions
later. Costs: the auction allowance and commission, as the earnings rule. Each trade is also
measured against every stock of its size group bought at the same open and held as long.

## Cells

2 events × 2 sizes × 2 holds = **8**, family `dividend_signal`.

## What counts

Search 2010–2017: over the average stock of its size, **1% a trade for 20 sessions, 2% for
60**, a weekly t (of that) of 3, six years of eight, and a positive average after costs; 100
trades (fewer reported and taken on if the rest is met). Tests on 2005–2009 and 2018–2022,
each cell that goes forward run once: half those, t of 2.5, four years of five, in both. 2023
is a check. The holdout stays sealed.
