# Extended-hours execution for the closing-unwind test

Request to the owners of `kinn.engine`, `kinn.run`, costs and
reporting. The owner's latest instruction is to research earlier
signals, shorter exits and after-hours trading at position sizes
below $5,000. The original brief forbids GPT from editing
`src/kinn/`, and AGENTS.md plus OWNERS.md assign these modules
to Claude. This request changes no platform code.

The concrete candidate is preregistered in
`strategies/close_unwind_impact_decay/HYPOTHESIS.md`.
It uses the change in price impact across two three-minute
windows after a large post-close decline. Its entry target
is $2,000 and its intended holding period is 15 minutes.
There are no historical alpha results for this candidate yet.

## Confirmed current behavior

- `load_day` retains minute bars but sets DayView open and
  close to the regular-session calendar.
- `simulate_signal` clamps entry to that open and stops
  processing bars at that close.
- `event_study.measure` uses the same boundaries and caps
  horizons at the regular-session official close.
- The runner exposes no extended-session configuration.
  Negative flatten or entry-cutoff settings cannot change
  those regular-session fill boundaries.
- The existing passive limit model cannot represent an
  aggressive limit with marketable spread and impact costs.
  IBKR's US stock market orders are restricted to regular
  hours. Extended-hours simulation needs limit semantics.
  [IBKR order types](https://www.interactivebrokers.com/support/faq/content/did-market-stop-order-u-35803691)

## Required behavior for this test

1. Add a versioned session configuration to the registered run
   path that permits entries from 16:08 through 17:01 ET and
   liquidation through the last extended-hours bar before
   20:00. Retain the calendar's regular-session close so that
   the strategy can skip early closes and form its reference.
   Record the execution profile in the manifest and config hash.
2. Keep next-clock-minute eligibility, one-minute entry expiry,
   volume participation, capital reservations and same-day
   accounting. An after-hours order cannot use the earlier
   regular-session auction for valuation or execution.
3. Support the candidate's aggressive limit cap and charge
   marketable fees and slippage. For the initial conservative
   bar approximation, allow opening fills only when modeled
   execution is within the cap. A next-bar high or low alone
   cannot create an immediate opening fill.
4. Support the timed liquidation and its retrying sell limits.
   Record unresolved shares, last observed valuation and
   failure to flatten, including positions with no later bar.
   Such positions must remain visible in risk reporting.
5. Give study horizons and portfolio fills the same session and
   expiry contract. The proposed initial extended-hours profile
   multiplies regular modeled slippage by two. Its reported 2×
   stress multiplies this extended baseline again. Fees stay
   at the selected calibration.
6. Test premarket and after-hours boundary bars, daylight saving,
   early closes, missing bars, nonmarketable price caps, partial
   fills, capital reservations, expiry, stale price references,
   liquidation retries and prefix replay. The default regular
   session behavior must retain its existing results.

The already built minute data include extended hours. The request
needs no raw download or bars rebuild. Quote samples around
eligible development events can check the fallback cost profile
once a counted run supplies candidate windows. Raw downloads
remain an owner action under the original brief.

Rechecked the remote `agent/claude/intraday-entry` branch at
`2cc002a`. It adds separate after-hours research scripts. The
registered intraday runner and fill model still use their
regular-session boundaries, so this execution request remains
pending for the candidate.
