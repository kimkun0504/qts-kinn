# Test intraday shorts with point-in-time stock loan data

Request for the owners of the data, engine, costs, risk and run manifest lanes.

The long-only minute engine cannot test the sell side of the large premarket
moves described in the recent search. That work suggests that some large
runners subsequently decline. Its estimates omit the entry eligibility, loan
charges and short-sale fills that could remove the effect. Decision 0010
defers shorts until a strategy needs borrow and locate rules.
[Recent-search report](https://github.com/kimkun0504/qts-kinn/blob/19a087de5381aa349fc04f9b6067460101bf876b/strategies/recent_search/REPORT.md)
· [Decision 0010](../decisions/0010-long-only-and-other-phase-2-deferrals.md)

## Data sample to request first

- Timestamped IBKR shortable-share snapshots, resolved to the security on
  that date, plus an indication of stale or missing observations. Sample
  qualifying signal dates before looking at returns and include delisted
  names and reported zero quantities. Record the feed's publication and
  receipt conventions. A snapshot is indicative. Keep actual broker
  locate outcomes or locate charges separately when they exist.
- Historical borrow-rate snapshots or fee records, any applicable locate
  charges, and broker margin requirements. For an intraday position, confirm
  the broker's actual billing convention. A daily rate can be used for a
  retrospective charge when applicable. A rate first published after entry
  cannot determine which orders were admitted. Short interest measures
  outstanding positions and cannot establish what was available to borrow.
  [IBKR stock-loan availability](https://www.interactivebrokers.com/support/faq/content/monitoring-stock-loan-availability-1163250499)
- Exchange short-sale restriction state or effective trigger records and
  timestamped trades and national best bid/offer around candidate entry and
  exit windows. When Rule 201 is in force, its price restriction generally
  applies for the rest of the trigger day and the following trading day.
  Eligible transactions and quote timing matter. Use the default restriction
  for an ordinary non-exempt order. Record fills and rejections separately.
  [SEC Rule 201 FAQ](https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions-7)

QuantRocket documents IBKR share availability at 15-minute intervals,
special margin flags and daily borrow fees, with history beginning in 2018.
This is a source to check for a small pre-seal feasibility sample. The
documented history does not cover Kinn's normal development years. Daily
fees are insufficient for screening on an intraday indicative rate. Check
coverage on the candidate universe and sample dates before any purchase
or implementation. Decision 0019 applied to the earlier recent-search
family. Its date split cannot be inherited for a new official run. Evidence
from those years informed the idea, so it cannot provide independent validation
of the same signal.
[QuantRocket data catalog](https://www.quantrocket.com/data/#interactive-brokers-shortable-shares)
· [Short-sale data guide](https://www.quantrocket.com/docs/#ibkr-short-sale-data-guide)
· [Decision 0019](https://github.com/kimkun0504/qts-kinn/blob/19a087de5381aa349fc04f9b6067460101bf876b/docs/decisions/0019-recent-years-search.md)

## Minimal Kinn support if the data are adequate

- Add an explicit short entry and corresponding buy-to-cover to the normal
  intraday engine. Give each simulated order the latest broker inventory and
  margin state known by its live timestamp. Reject absent, stale or
  insufficient locates under the registered fill model. For a restricted
  marketable entry, require a permitted fill supported by the available
  quote and trade observations. Preserve chronological reservation and
  share participation. Use $20,000 buying power and a $2,000 target subject
  to broker specific margin limits. Cover in the same session. Track any
  unresolved cover as an execution failure.
- Keep fees, slippage and stock-loan charges as separate fields. Double
  slippage only in the stressed case. Record stock-loan and restriction data
  versions in the manifest. Count rejected signals by reason and report
  their share of the candidate universe, so scarce locates cannot quietly
  create a selected sample of winning trades.
- Add synthetic tests for denied and exhausted inventory, a future
  stock-loan update hidden on replay, next-clock-minute activation,
  short-sale restriction carryover, margin rejection, buy-to-cover price
  gaps, halts and same-day liquidation. Preserve the existing long-entry
  tests. Require an owner-approved data split and a committed hypothesis
  before measuring returns through `kinn run`.

First establish feasibility with read-only data through 2023-11-08. Data
acquisition, platform changes and any change to the date split require the
owner. The sealed holdout stays excluded. This request contains no new
strategy run or return estimate.
