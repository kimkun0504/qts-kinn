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
| `strategies/<new>` | whoever claims it | | one owner per strategy |
| `research/claude` | claude | | sandbox |
| `research/gpt`, `research/external` | gpt | | sandbox; Astra's delivery lands in `external/` |
| `docs/`, repo config, CI | owner (Kun) | 2026-11-15 | agents propose by PR |

Claude built every platform module in Phases 0–4, so it holds those lanes today. The owner
reassigns lanes here when the GPT agent starts work.
