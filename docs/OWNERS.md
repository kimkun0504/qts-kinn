# Owners (lane locks)

One owner per platform module at a time. To take a lane, change this table in your pull request.
To ask for a change in a lane you don't own, add a note under `docs/requests/`.

| Module / strategy | Owner | Since | Note |
|---|---|---|---|
| `kinn.core` | claude | 2026-11-15 | |
| `kinn.data` | claude | 2026-11-15 | |
| `kinn.features` | claude | 2026-11-15 | |
| `kinn.costs` | claude | 2026-11-15 | |
| `kinn.risk` | claude | 2026-11-15 | |
| `kinn.engine` | claude | 2026-11-15 | |
| Extended-hours execution in `kinn.engine.intraday`, `kinn.run`, `kinn.validation.event_study`, and execution-risk reporting | gpt | 2026-11-17 | Owner explicitly authorized the scoped changes in chat; regular-session behavior retained. This temporary sub-lane overrides the broader rows for this change only. |
| Transaction-count field in `kinn.engine.intraday.data` and its replay tests | gpt | 2026-11-18 | Owner explicitly authorized the scoped existing-column view change in chat; no ingestion or build changes. |
| `kinn.validation` | claude | 2026-11-15 | open to gpt on request |
| `kinn.registry`, `kinn.run`, `kinn.cli` | claude | 2026-11-15 | |
| `kinn.reporting` | claude | 2026-11-15 | open to gpt on request |
| `apps/workbench` | claude | 2026-11-15 | open to gpt on request |
| `strategies/intraday_rebound` | claude | 2026-11-15 | parked; see its REPORT.md |
| `strategies/random_entry` | claude | 2026-11-15 | canary; change only with the canary tests |
| `strategies/rebound_limit` | claude | 2026-11-16 | parked: failed the holdout; reversal signals and fast-fall entries did not reach the target, see its REPORT.md |
| `strategies/intraday_momentum` | claude | 2026-11-16 | development study and fill measurement done: marginal, owner to decide; see its REPORT.md |
| `strategies/recent_search` | claude | 2026-11-16 | parked: 2,689 cells on 2018–2022 incl. timed news, no long candidate; see its REPORT.md |
| `strategies/swing_search` | claude | 2026-11-16 | event-study: rule A50 (earnings drift, $50M–$300M) passed its tests on 2005–2009, 2018–2022 and 2023; auction fills not yet measured |
| `strategies/earnings_drift` | claude | 2026-11-16 | developing: rule A50 passed its one holdout run (owner, 2026-11-16); fills measured from ticks; not yet traded |
| `strategies/insider_buying` | claude | 2026-11-16 | event-study: rule I passed its pre-holdout tests; about 1.5% a trade since 2018; holdout untouched |
| `strategies/intraday_rebound_passive` | claude | 2026-11-15 | tick study; not established |
| `strategies/momentum_12_1` | claude | 2026-11-15 | daily; parked |
| `strategies/opening_gap_continuation` | gpt | 2026-11-15 | opening gap continuation, long only |
| `strategies/opening_gap_reclaim` | gpt | 2026-11-15 | overnight gap reversal |
| `strategies/filing_session_momentum` | gpt | 2026-11-15 | filing-related intraday momentum |
| `strategies/intraday_volume_surge` | gpt | 2026-11-15 | small-cap turnover surge continuation |
| `strategies/rebound_confirmed_recovery` | gpt | 2026-11-15 | buy after a deep selloff starts recovering |
| `strategies/earnings_gap_followthrough` | gpt | 2026-11-16 | intraday confirmation after a typed earnings disclosure |
| `strategies/insider_price_reclaim` | gpt | 2026-11-16 | rebound anchored on a disclosed purchase price |
| `strategies/heavy_turnover_stabilization` | gpt | 2026-11-17 | rebound after an active stabilization phase |
| `strategies/equity_sale_gap_reclaim` | gpt | 2026-11-17 | gap recovery after a typed equity sale filing |
| `strategies/small_cap_attention_rotation` | gpt | 2026-11-17 | delayed momentum in an active small-cap cohort |
| `strategies/distributed_morning_selloff` | gpt | 2026-11-17 | recovery after a decline spread across the morning |
| `strategies/late_rally_selloff` | gpt | 2026-11-17 | rebound after a selloff in a late-session rally |
| `strategies/one_dollar_reclaim` | gpt | 2026-11-17 | rebound above a fixed nominal price after an intraday break |
| `strategies/filing_aware_dislocation` | gpt | 2026-11-17 | exclude newly usable filings from the size-peer reversal |
| `strategies/close_unwind_impact_decay` | gpt | 2026-11-17 | frozen after-hours impact-decay study; scoped execution support authorized |
| `strategies/premarket_price_discovery` | gpt | 2026-11-18 | distributed premarket price discovery, one frozen momentum rule |
| `strategies/auction_gap_repair` | gpt | 2026-11-18 | opening discount to an active premarket reference, one rebound rule |
| `strategies/earnings_trade_size_shift` | gpt | 2026-11-18 | typed earnings and expanding trade size; count view authorized and tested |
| `strategies/fragmented_selloff_exhaustion` | gpt | 2026-11-18 | smaller-print selloff exhaustion with a frozen unfiltered control |
| `strategies/quiet_size_breakout` | gpt | 2026-11-18 | larger-print narrow-range breakout at one fixed clock time |
| `strategies/<new>` | whoever claims it | | one owner per strategy |
| `strategies/active_gap_recovery` | gpt | 2026-11-18 | recovery after a dense-trading stock resumes at a discount; missing bars are a proxy only |
| `research/claude` | claude | | sandbox |
| `research/gpt`, `research/external` | gpt | | sandbox; Astra's delivery lands in `external/` |
| `docs/`, repo config, CI | owner (Kun) | 2026-11-15 | agents propose by PR |

Claude built every platform module in Phases 0–4, so it holds those lanes today. The owner
reassigns lanes here when the GPT agent starts work.
