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
| `strategies/rebound_limit` | claude | 2026-11-15 | developing; `s_l468` passed validation, see its REPORT.md |
| `strategies/intraday_rebound_passive` | claude | 2026-11-15 | tick study; not established |
| `strategies/momentum_12_1` | claude | 2026-11-15 | daily; parked |
| `strategies/opening_gap_continuation` | gpt | 2026-11-15 | opening gap continuation, long only |
| `strategies/opening_gap_reclaim` | gpt | 2026-11-15 | overnight gap reversal |
| `strategies/filing_session_momentum` | gpt | 2026-11-15 | filing-related intraday momentum |
| `strategies/intraday_volume_surge` | gpt | 2026-11-15 | small-cap turnover surge continuation |
| `strategies/rebound_confirmed_recovery` | gpt | 2026-11-15 | buy after a deep selloff starts recovering |
| `strategies/relative_dislocation_reversal` | gpt | 2026-11-16 | active stocks, relative intraday reversals |
| `strategies/gap_washout_reclaim` | gpt | 2026-11-16 | positive gap, selloff and VWAP reclaim |
| `strategies/turnover_compression_breakout` | gpt | 2026-11-16 | high-turnover range and confirmed breakout |
| `strategies/volume_surge_pullback` | gpt | 2026-11-16 | recovery after a high-turnover surge pulls back |
| `strategies/opening_premarket_discount` | gpt | 2026-11-16 | recovery from an opening discount to premarket trades |
| `strategies/market_recovery_lag` | gpt | 2026-11-16 | delayed stock recovery after a broad selloff |
| `strategies/<new>` | whoever claims it | | one owner per strategy |
| `research/claude` | claude | | sandbox |
| `research/gpt`, `research/external` | gpt | | sandbox; Astra's delivery lands in `external/` |
| `docs/`, repo config, CI | owner (Kun) | 2026-11-15 | agents propose by PR |

Claude built every platform module in Phases 0–4, so it holds those lanes today. The owner
reassigns lanes here when the GPT agent starts work.
