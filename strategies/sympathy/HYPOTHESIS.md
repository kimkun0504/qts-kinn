# Sympathy: the peers of a company that collapsed on its results

Written 2026-11-17 23:15 ET, before anything is measured. The lead of the night: a company of $300M or more
down 15% or more after hours on its results keeps falling to the next open. Its industry peers,
with no news of their own, often open lower too: people sell the industry on the headline. If
that is mostly reflex, the peers that gap down should come back during the session. It is a
long trade, which needs no borrow.

## Events

**Trigger:** a results 8-K accepted after the close of session D in a company of $300M or
more whose stock is down 15% or more half an hour later (the after-hours events of
`after_hours`, any size of $300M or more). **Peers:** listed common stock in the same
industry (the vendor's industry, as in the daily table), $300M or more, $1M a day, a close of
$5 or more, no results due that night (`night_bids`' results nights), not the trigger.

## Trade

A peer that **opens D+1 at least 2% (or 3%) under its close of D**: bought at D+1's open, sold
at D+1's close, or at the close 5 sessions later. One trade a peer a day however many triggers
it has. Costs: the auction allowance and commission.

## Cells

2 gaps × 2 holds = **4**, family `sympathy`.

## What counts

Search 2010–2017: 0.3% a trade after costs for the one-session hold, 1% for five; weekly t of
3; six years of eight; 150 trades. Tests on 2005–2009 and 2018–2022, each cell that goes
forward run once: half those, t of 2.5, four years of five, in both. 2023 is a check. The
holdout stays sealed.

**Results, 2026-11-17 23:16 ET.** **None of the 4 cells meets the bar; the peers keep falling.** 46,475
peer-days; 2,564 opened 2% or more down. Bought at that open: −1.01% by the close and −1.48% in
five sessions (2% gap); −1.28% and −1.82% (3% gap); two or three years of eight positive. Bad
news about an industry spreads slowly, as it does for the company itself. 4 trials.

## Addendum, 2026-11-17 23:16 ET: the other direction, bought

Written before it is measured, after seeing that peers continue in the direction of their gap
on bad news. If good news also spreads slowly, the peers of a company that **jumps** 15% or more
after hours on its results, which **open 2% (or 3%) or more higher**, should keep rising.
Trigger: the after-hours events of `after_hours` with a rise of 15% or more, $300M or more.
Peers, trade, costs and bar as above (bought at the open, sold at the close or five sessions
later). **4 cells**, charged to `sympathy`.
