# 0016 — What the daily engine does not model yet

**Status:** accepted, 2026-11-15 (claude). Each item is a known gap, recorded so it is not
mistaken for a result.

| Not modelled | What is assumed instead | Matters when |
|---|---|---|
| Margin calls and forced deleveraging | Limits apply at each rebalance only; exposure drifts in between (optional `rebalance_if_gross_above`) | a leveraged book falls fast (2009) |
| Borrow availability and rates by stock | Every stock above $1 billion can be shorted at 1% a year | crowded or small shorts |
| Interest on cash and on short proceeds | None either way | rates are high |
| The price impact of the book's own orders | Auction slippage of 10 bps, order capped at 1% of daily volume | the account grows |
| Cash in lieu, rights, tender offers | Splits round to whole shares; a company that stops trading is closed at its last price with a 2% cost | rarely |
| 2× slippage re-sizing the book | 2× subtracts the extra slippage from each day's P&L | costs are large |
| A tearsheet file for book runs | `metrics.json` and the Workbench page | reading results without the Workbench |
