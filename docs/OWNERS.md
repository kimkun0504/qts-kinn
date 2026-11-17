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
| `strategies/short_search` | claude | 2026-11-17 | short sales held one to three weeks (owner allowed short research 2026-11-17) |
| `strategies/news_hours` | claude | 2026-11-17 | the hours and days after an 8-K becomes public (SEC acceptance times) |
| `strategies/<new>` | whoever claims it | | one owner per strategy |
| `research/claude` | claude | | sandbox |
| `research/gpt`, `research/external` | gpt | | sandbox; Astra's delivery lands in `external/` |
| `docs/`, repo config, CI | owner (Kun) | 2026-11-15 | agents propose by PR |

Claude built every platform module in Phases 0–4, so it holds those lanes today. The owner
reassigns lanes here when the GPT agent starts work.
