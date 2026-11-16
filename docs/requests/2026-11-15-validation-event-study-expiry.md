# Honor market entry expiry in event studies

`kinn.validation.event_study.measure` finds the first bar at or after the order becomes live
and enforces the session entry cutoff. The portfolio engine also applies `Signal.expire_minute`.
For a one-bar order, this difference lets the study measure delayed fills the portfolio engine
would reject. In run `20261116T002542Z_gpt_opening_gap_continuation_9db697d9`, 54 of the 8,483
stored events entered after the registered expiry.

Apply the signal expiry as an inclusive entry cutoff for the study's market-order events,
using the earlier of expiry and the existing session cutoff. Keep the current behavior for
signals with no expiry. A fixture with a missing first eligible bar and a later print would
exercise the change.
