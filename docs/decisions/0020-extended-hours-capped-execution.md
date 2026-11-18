# Opt-in extended-hours capped execution

Owner authorization: in this research chat the owner explicitly
authorized GPT to implement the scoped platform changes requested
in `docs/requests/2026-11-17-extended-hours-execution.md`.

`fills.session: extended_v1` enables execution on observed bars
from 04:00 up to 20:00 New York time. Regular-session calendar
bounds in DayView retain their meaning. Explicit entry bounds
in the configuration govern admission. The profile is included
with resolved defaults in both the manifest and config hash.
Existing regular-session defaults retain their fill rules.

Only capped buy limits with an expiry and a timed liquidation
are supported. Stops and targets are rejected. Opening-only
fills require the modeled opening execution price at both 1×
and 2× slippage to fit the cap. Prices and slip dollars are
recorded separately, as for regular fills. Both cases use the
same conservative fills; costs are not an independent source
of extra cap violations. There is no later-low opening fill.

At the holding deadline, the engine submits a sell limit a
configured fraction below the preceding observed positive-volume
close. Each next-minute retry uses the close then available;
missing bars cannot fill, and stale references are allowed but
retain their price cap. Partial fills respect participation.
Each filled replacement order pays a fresh commission minimum.

Any unsold shares at 20:00 remain unresolved. They reserve
capital for the rest of the session and remain in entry-count
and daily-loss checks. They are not completed trades. The run
stores their filled shares, residual quantity, costs and last
positive-volume mark. `unresolved.parquet` and
`marked_equity.parquet` expose that valuation, distinct from
the completed-trade equity curve. Any unresolved exposure
invalidates a same-day strategy; the simulation's independent
session results cannot be treated as a realizable flat book.
Part-file counts must agree with the unresolved records.

The extended event study uses the exact same single scheduled
holding policy as the portfolio. Its horizon denotes when
liquidation starts. Completion can occur later; an unresolved
event stays in the table with a null completed return and
invalidates advancement. This differs from the legacy regular
event-study return curve, whose behavior is preserved.

The calibration remains `ibkr_pro_tiered`; the extended baseline
multiplies its marketable spread and impact estimate by two,
and the usual stress doubles that baseline again. Fees remain
as calibrated. The multiplier is an assumption, not measured
extended-hours spreads. The full minute's range and volume
approximate execution costs and capacity after signal formation;
they cannot establish depth or an attainable opening fill.
Quote and tick checks remain necessary before a trading claim.

No data build or download is part of this change.
