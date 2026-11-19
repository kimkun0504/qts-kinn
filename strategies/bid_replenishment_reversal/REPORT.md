# Bid replenishment reversal

## Verdict: park — frozen quote-coverage gate failed

The price-only control establishes a sufficient candidate pool
for the registered quote experiment: 1,933 events on 937 dates,
including 406 events in 2013–2016. Its mean net is
+0.72% at base costs and +0.40% at doubled
slippage. The control cannot replace the primary and supplies
no evidence of a +3% mean trade.

The bid-replenishment predicate was committed before the control
run or any quote-window selection/inspection. It has not been
tested on actual quotes. No primary portfolio or validation run
has been performed, and no quote threshold was selected from
these control returns.

## Control run and trial accounting

- `20261119T043722Z_gpt_bid_replenishment_reversal_91e8fd86`,
  completed event study on 2003-09-10 through 2016-12-30.
- Hypothesis commit `127f7c4`; clean run commit `031c811`;
  agent `gpt`, data build `447e58e098`;
  `ibkr_pro_tiered`, $20,000 account and $2,000 target.
- One additional `intraday_rebound` trial; family total
  112, including nine earlier declared looks.
  At most three further performance runs remain registered:
  primary study, primary development portfolio, one primary
  validation if all earlier gates pass.
- Necessary acquisition gate: at least 150 control events on
  90 dates and 40 in 2013–2016. Passed. There is no return
  gate selecting a quote definition from the control.

## Control diagnostics at the registered r_120 horizon

| Window | Events | Active dates | Gross mean | Net mean, 1× | Net mean, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 1933 | 937 | +1.23% | +0.72% | +0.40% |
| 2013–2016 | 406 | 281 | +0.55% | +0.12% | −0.13% |

| Full control | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| Total modeled event P&L | $27,609 | $15,422 |
| Daily P&L t-statistic | 2.64 | 1.51 |
| Worst end-of-day drawdown | −$4,522 | −$7,544 |
| 95% day-clustered mean-net interval | +0.23% to +1.21% | −0.09% to +0.90% |
| Winners | 1072 | 1019 |
| Mean winner | +6.20% | +6.22% |
| Losers | 861 | 914 |
| Mean loser | −6.11% | −6.09% |

The full gross interval is +0.74% to
+1.73%. Mean target notional was $1,992.
Fees remain fixed when slippage doubles.

One event entered after its permitted next clock minute because
the normal study ignores expiry. The 1,932 on-time events average
+0.72% base and +0.41%
stressed. The later block's 406 events are all on time.
Eighty-three targets exceeded 5% of entry-bar volume. Both
limitations will be checked on the primary's saved event rows,
then with actual simulated constraints in a qualifying portfolio.

The run recorded 937 signal-day lookahead checks. Daily P&L sums
each independent event's modeled net dollars over all sessions
in the run manifest, including zero-event dates; drawdown starts
from the initial zero. This is not a capital-constrained account
portfolio. No quote-based execution has been tested.

## Control by development year

| Year | Events | Net mean, 1× | Net mean, 2× | Event P&L, 1× | Event P&L, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 15 | −0.20% | −0.36% | −$61 | −$111 |
| 2004 | 77 | +1.66% | +1.42% | $2,543 | $2,171 |
| 2005 | 51 | −0.31% | −0.57% | −$305 | −$574 |
| 2006 | 49 | +0.91% | +0.68% | $881 | $663 |
| 2007 | 171 | +0.95% | +0.66% | $3,240 | $2,252 |
| 2008 | 784 | +0.95% | +0.56% | $14,766 | $8,767 |
| 2009 | 167 | +0.72% | +0.38% | $2,389 | $1,262 |
| 2010 | 43 | +1.89% | +1.62% | $1,614 | $1,381 |
| 2011 | 89 | +0.54% | +0.30% | $951 | $521 |
| 2012 | 81 | +0.37% | +0.11% | $595 | $173 |
| 2013 | 52 | +1.24% | +0.99% | $1,285 | $1,024 |
| 2014 | 95 | −1.00% | −1.27% | −$1,903 | −$2,417 |
| 2015 | 129 | +0.48% | +0.24% | $1,237 | $608 |
| 2016 | 130 | +0.14% | −0.12% | $377 | −$301 |

## Frozen acquisition plan

Every control event is in the plan. There is no sampling by
return, fills or existing quote availability. The planner reads
day, company, symbol, signal minute and pre-open metadata;
forward returns and future entry prices are omitted from that
read. The downloader-compatible entry_price field is explicitly
a prior-close placeholder, not an execution assumption.

- Schema `bid-quote-plan-1`; planner commit `9d6b83c`.
- Plan directory:
  `/Users/kkim/Desktop/QTS/MarketData/processed/kinn/quotes_sample/gpt_bid_replenishment_20261119T043722Z/`
- `windows.csv`: all 1,933 twelve-second windows [T−10s,T+2s).
  Fixed feature targets: T−5 seconds and T−1 nanosecond.
- CSV SHA-256:
  `13c1c4b001d303b001c076173d186144d2fa39348da00023cfd1e320f7f4bfd2`.
- `plan.json` pins source manifest/events hashes and timing.
  An existing plan with different content or a modified CSV
  is refused, rather than silently overwritten.
- File-presence inspection found no requested quote file in
  this new raw plan directory. No quote price was read.

The owner action and exact existing download command are in
`OWNER_ACTIONS.md`. The scoped native input/index request is
`docs/requests/2026-11-18-nbbo-replenishment-input.md`.
The owner authorized the adapter and separate index in chat. The
native adapter is now implemented; the historical windows are still
required. The latest file-presence check found none in the requested
raw plan directory. No primary result exists yet.
GPT has not downloaded, written, moved or copied raw data.

## Tests, provenance and limits

Focused strategy/configuration/repository checks and acquisition
planner subprocess tests passed, as did lint and import contracts.
They cover quote-size/spread boundaries and unit invariance,
one-second freshness, future-quote rejection, causal prefixes,
failed-first-event handling, an intentional future-pair canary,
all-event enumeration, omitted outcomes, DST, raw-output refusal
and immutable CSV checks. Strategy replay now uses native immutable
QuoteSnapshot/BookPair values and DayView, replacing the proposed
contract fixture. Native synthetic builder/store/runner tests also
check source hashes, every-parent retention, missing versus empty files,
invalid latest observations, conflicting ties, no post-decision feature
use, identity/time errors, native future canaries, immutable planning,
and pinned resume/spawn behavior. Software tests do not establish
actual quote availability, executable depth or latency.

All empirical performance diagnostics above derive from the
completed control's manifest and r_120 event rows. The plan
is acquisition metadata and supplies no new performance result.
No primary, validation, post-seal market query, raw write,
download or bar/panel rebuild was performed.

The quote signal could reflect fleeting public orders and
withdrawals rather than buying. Common-unit ratios do not
establish absolute executable size or firm depth. SIP timestamp
and assumed freshness do not measure client latency. The
primary retains the ordinary bar execution and cost assumptions;
the signal does not verify fills.

Earlier rebound and momentum searches, failed validation of the
old trend filter, and the documented documentation-sample
exposure remain part of the research history. No new quotes
can erase the broader adaptive search or restore pristine
validation. The primary is untested until the owner dependency
is resolved.


## Authorized adapter implementation (2026-11-19)

The scoped native input `nbbo_replenishment` / `nbbo-replenishment-1`
now has typed views, a separate immutable snapshot builder, source and
raw content fingerprints, per-period/year coverage, strict date/window
checks and pinned runner manifests. All parent candidates survive even
when snapshots are unavailable. The complete development source plan
passed native identity/time/hash validation; no raw quote price was read
in that check. A missing file refuses publication of the index.

The source strategy file is unchanged from the preregistered control
commit. New runs enforce that equality, and workers enforce the
run-created strategy hash. A high-level price-only planning path is
implemented for a potential later validation acquisition; it computes
no forward measurements or P&L. It has been tested only on synthetic
fixtures. No real validation planning or performance run was performed.

No additional empirical trial was used for implementing/testing the
adapter. The one control run and its trial accounting remain as above.
The primary waits for owner acquisition before its one registered
study. A coverage failure will not be repaired by changing the frozen
signal, dropping difficult events or selecting a different period.

Verification: the full suite passed (710 tests), with Ruff lint/format
checks and all five import contracts passing. These are software checks,
not added research trials or performance observations.


## Final acquisition and coverage verdict (2026-11-19)

Every planned file arrived. From clean commit `65cb31c`, the authorized
separate builder published input `2738076d4b` (`nbbo-replenishment-1`)
against data build `447e58e098`. Every control identity and first signal
minute is retained. The input metadata fingerprints all raw sources,
plan/control artifacts and parser version. Pairs SHA-256:
`8695dd2b7a90fafb682e6dbd89ad886400b42f30872c4d366a7ca38a96b0ec60`.
GPT changed no raw file and performed no bar/panel rebuild.

| Window | Parents | Valid pairs | Coverage | Frozen minimum | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Full development | 1933 | 725 | 37.51% | 95% | Fail |
| 2013–2016 | 406 | 180 | 44.33% | 95% | Fail |

| Year | Parents | Valid pairs | Coverage |
| --- | ---: | ---: | ---: |
| 2003 | 15 | 0 | 0.00% |
| 2004 | 77 | 3 | 3.90% |
| 2005 | 51 | 9 | 17.65% |
| 2006 | 49 | 17 | 34.69% |
| 2007 | 171 | 69 | 40.35% |
| 2008 | 784 | 290 | 36.99% |
| 2009 | 167 | 65 | 38.92% |
| 2010 | 43 | 19 | 44.19% |
| 2011 | 89 | 44 | 49.44% |
| 2012 | 81 | 29 | 35.80% |
| 2013 | 52 | 23 | 44.23% |
| 2014 | 95 | 39 | 41.05% |
| 2015 | 129 | 57 | 44.19% |
| 2016 | 130 | 61 | 46.92% |

Unavailable targets include 868 stale, 611 conflicting, 109 missing
and 63 invalid observations. These are nonexclusive target counts,
not disjoint event counts. Conflicting latest timestamps remain
unavailable as registered; no sequence-field or favorable-quote
tie-break was added. Freshness remains one second. File presence
does not establish valid-pair coverage.

The preregistered missingness diagnostic joins the saved control's
r_120 rows to this input. These are control cohorts, not the
replenishment primary or a newly eligible strategy. Saved event
fees and slippage are return fractions; net subtracts them directly.

| Control window / quote availability | Events | Dates | Mean net, 1× | Mean net, 2× |
| --- | ---: | ---: | ---: | ---: |
| Full / available | 725 | 472 | +1.05% | +0.78% |
| Full / unavailable | 1208 | 680 | +0.52% | +0.18% |
| 2013–2016 / available | 180 | 151 | +1.02% | +0.79% |
| 2013–2016 / unavailable | 226 | 181 | −0.59% | −0.87% |

The performance diagnostics derive solely from control run
`20261119T043722Z_gpt_bid_replenishment_reversal_91e8fd86` and its
saved event rows. Coverage numbers are input/acquisition metadata,
not performance results. Availability alone selects a different
control-return distribution, especially in later development;
discarding unavailable parents would conceal that selection.

**Park before the primary study:** both mandatory input gates fail.
No primary returns are needed to reject eligibility. No primary
performance run, portfolio, validation plan or validation performance
run was made. Exact primary/control return matching is therefore
not applicable. No timestamp policy, threshold, freshness or period
was relaxed. The experiment used one empirical trial, the control;
`intraday_rebound` remains at 112 counted/declared trials here.

This is insufficient coverage for the frozen experiment, not proof
that replenishment has negative expected returns. The acquired index
remains available for audit. The signal is not rescued by changing
its observation rules after seeing coverage. Earlier pending-status
paragraphs describe the chronology; acquisition is now complete.
