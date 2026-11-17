# 0022 — The Workbench is organised by strategy, and strategy.yaml carries the record

**Status:** owner's instruction, 2026-11-17 ("does it hold all the tests we've done, does it
organize well. I want a high quality product"; the mockup was approved the same day, light
theme as the default).

**Context.** The Workbench listed runs. Most of the research was not in it: searches done by
research scripts never became runs, the one strategy that passed its holdout was not marked,
the paper ledger and the reports were not shown, and the page a reader landed on was a table
of 142 runs.

**Decision.**

- The Workbench opens on what works, what is being tested forward, what waits on the owner and
  every idea tested with its verdict. Each idea has a page: results, trades, paper book,
  report, studies, runs. Runs, Compare, Parameters and Trials stay as they were.
- The verdicts and the studies are written by hand in a `record:` block in each
  `strategies/<name>/strategy.yaml`. It sits beside the hypothesis and the report, is reviewed
  in the same pull request as the verdict, and needs no database. `apps/workbench/record.py`
  joins it to the run store.
- Numbers shown for a period (profit, Sharpe, drawdown, months, targets) are computed from the
  run the record names. The record's text is not checked against the runs.
- The paper ledger writes `snapshot.json` each night; the Workbench reads that and never
  recomputes the books. Until the first snapshot it falls back to `state.json` and the report.
- Light is the default theme. Gains are teal and losses red, a pair that stays apart for
  colour-blind readers in both themes; every gain or loss also carries its sign.

**Consequences.** A verdict now has two places to update, REPORT.md and the record; a stale
record shows a stale home page. The Workbench still only reads: it starts no run and sends no
order. Astra's strategies have no record yet and are listed under "Astra's ideas" with their
run counts until Astra writes one.

**Deferred.** Launching runs from the Workbench; checking the record's text against its runs;
a benchmark line on the profit chart.
