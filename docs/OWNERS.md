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
| `strategies/foreign_drift` | claude | 2026-11-17 | the earnings rule in companies that report on 6-K (measured 2026-11-17; closed) |
| `strategies/stake_filings` | claude | 2026-11-17 | buying after a Schedule 13D (measured 2026-11-17; closed) |
| `strategies/deal_spread` | claude | 2026-11-17 | takeover targets held to the close of the deal (measured 2026-11-17; closed) |
| `strategies/etf_trend` | claude | 2026-11-17 | trend following across asset-class index funds |
| `strategies/after_hours` | claude | 2026-11-17 | buying an earnings reaction in extended hours, small size (owner's idea) |
| `strategies/runner_close` | claude | 2026-11-17 | a stock that has run on the day, into the close and overnight (owner's observation) |
| `strategies/night_bids` | claude | 2026-11-17 | resting buy orders below the close in after-hours, sold at the next open (owner's idea) |
| `strategies/before_report` | claude | 2026-11-17 | buying ahead of results, chosen by the company's own record of reactions (owner asked for earlier entries) |
| `strategies/read_across` | claude | 2026-11-17 | the unreported industry peers of a company that jumped on results (owner asked for earlier signals) |
| `strategies/closing_bids` | claude | 2026-11-17 | limit-on-close buy orders under a stock pushed down in the last ten minutes, sold at the next open |
| `strategies/overnight_hold` | claude | 2026-11-17 | holding only overnight or only by day, by where a stock's gains have come (indicator of our own) |
| `strategies/overnight_offering` | claude | 2026-11-17 | the first session after a company sells new shares overnight (prospectus filings) |
| `strategies/lockup_end` | claude | 2026-11-17 | the weeks around an IPO's lockup end (insiders may first sell) |
| `strategies/filing_drift` | claude | 2026-11-17 | the earnings rule on 10-Q and 10-K filings of companies with no results 8-K |
| `strategies/intraday_shape` | claude | 2026-11-17 | first and last half-hour pressure over days, from minute bars (indicator of our own) |
| `strategies/holders13f` | claude | 2026-11-17 | small companies whose number of 13F holders jumped (13F data, 2013 on) |
| `strategies/earnings_model` | claude | 2026-11-17 | one fixed model of the drift after results, with intraday features |
| `strategies/late_filer` | claude | 2026-11-17 | buying when an overdue 10-Q or 10-K arrives after a late-filing notice |
| `strategies/friday_reports` | claude | 2026-11-17 | the earnings rule on results first read on a Friday (inattention) |
| `strategies/rebalance_flows` | claude | 2026-11-17 | stocks against bonds in the last days of the month (fund rebalancing) |
| `strategies/dividend_signal` | claude | 2026-11-17 | dividend initiations and raises in small companies (Sharadar actions) |
| `strategies/five_dollars` | claude | 2026-11-17 | a small company back over $5 after months under it (fund and margin eligibility) |
| `strategies/ssr_day` | claude | 2026-11-17 | the session after the short-sale circuit breaker (Rule 201) trips, against near misses |
| `strategies/net_net` | claude | 2026-11-17 | Graham net-nets in small companies (balance sheet from raw SF1) |
| `strategies/insider_confirmed` | claude | 2026-11-17 | an insider purchase confirmed by a strong rise on volume within weeks |
| `strategies/leads_2023` | claude | 2026-11-17 | the once-only 2023 reading of four leads |
| `strategies/report_timing` | claude | 2026-11-17 | late and early results against the company's own calendar (Johnson and So) |
| `strategies/sympathy` | claude | 2026-11-17 | peers that gap down after an industry name collapses after hours on results |
| `strategies/first_report` | claude | 2026-11-17 | the drift after a new listing's first strong results |
| `strategies/uplisting` | claude | 2026-11-17 | a company that moves up to Nasdaq or the NYSE (Sharadar exchange changes) |
| `strategies/index_deletion` | claude | 2026-11-17 | companies dropped from the S&P 500 that stay listed |
| `strategies/spin_off` | claude | 2026-11-17 | newly spun-off companies and their parents |
| `strategies/self_tender` | claude | 2026-11-17 | companies filing an issuer tender offer |
| `strategies/after_hours_other` | claude | 2026-11-17 | large after-hours moves that are not results |
| `strategies/russell_move` | claude | 2026-11-17 | companies moving from the Russell 1000 to the Russell 2000 |
| `strategies/busy_day` | claude | 2026-11-17 | results jumps on crowded reporting days |
| `strategies/quarter_turn` | claude | 2026-11-17 | losers bought at the last close of a quarter |
| `strategies/bad_items` | claude | 2026-11-17 | shorts after 8-Ks with quiet bad news |
| `strategies/annual_timing` | claude | 2026-11-18 | 10-Ks filed much earlier than last year |
| `strategies/big_prints` | claude | 2026-11-18 | quiet up days traded in unusually large pieces |
| `strategies/<new>` | whoever claims it | | one owner per strategy |
| `research/claude` | claude | | sandbox |
| `research/gpt`, `research/external` | gpt | | sandbox; Astra's delivery lands in `external/` |
| `docs/`, repo config, CI | owner (Kun) | 2026-11-15 | agents propose by PR |

Claude built every platform module in Phases 0–4, so it holds those lanes today. The owner
reassigns lanes here when the GPT agent starts work.
