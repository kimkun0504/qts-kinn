# 0023 — The Lab: the owner's own algorithms, run on every stock from the Workbench

**Status:** owner's instruction, 2026-11-18 ("add a functionality in the research platform that I
can use to run my own algorithms based on all the data massive provides … a run button that runs
against all stocks and I need to be able to see which stocks performed well and which haven't …
plan thoroughly making sure to build it industry standard").

**Context.** Every result so far came from an agent: a research script or a `kinn run`. The
owner had no way to try an idea himself without asking for code. The Workbench only read the
run store; it could not start anything.

**Decision.**

1. **A Lab page in the Workbench.** The owner writes an algorithm in Python in the page (a code
   editor), picks the period, universe, exit and book settings, and presses Run. The result
   shows the summary, the profit curve, every year, the spread of trade returns, **every stock
   ranked from best to worst with its trades**, and the run history with its trial count.
2. **The algorithm is a function of the data.** `signal(data)` returns a table of dates by
   stocks: `True` where to buy (or a score, in ranking mode), computed on each day's close and
   acted on at the next open. An optional `exit_signal(data)` sells at the next open. Everything
   else (fills, stops, costs, book) is the Lab's, so every algorithm is judged the same way. The
   contract and the fields are in `docs/LAB.md`.
3. **The data is the platform's, through the sealed store.** Prices, volume, trade counts,
   market value, results and other 8-K filing days, and as-reported fundamentals come from
   `kinn.data.store.DataStore`, so **no date on or after the holdout start can be read** (the
   seal applies to the owner's runs exactly as to the agents'). Fundamentals are usable from the
   session after their filing date. Fields are loaded only when the code first asks for them.
4. **The engine is honest by construction.**
   - Next-bar execution: a signal on day *t* buys at the open of *t+1*; the universe test for
     *t+1* uses only what was known before that open (the previous close's market value and
     dollar volume).
   - **A lookahead test on every run:** the algorithm is run again on the data cut off at two
     dates; if its signals up to a cut-off change, it used the future, and the run is marked
     "The code looks ahead" in red with the first stock and day that changed. It cannot be
     switched off. Every field the Lab derives (the split-adjusted close is anchored at each
     stock's first price, not its last) passes the same test.
   - One position per stock at a time. Stops and targets are checked on each day's high and
     low; a gap through a stop fills at the open; when a stop and a target are both touched in
     one day, the stop is assumed first. A stock that stops trading is sold at its last close.
   - Costs from the platform's cost model (`kinn.costs`, IBKR Pro tiered): commission and fees
     on the real share count, the auction allowance at the open and close, the half-spread for
     stop and target fills. Every result is shown at 1× and 2× slippage; a result that is
     negative at 2× is marked fragile.
   - Each trade is also measured against the equal-weight average of the universe over the same
     days (the "over the average" figure the research uses), and the book against SPY.
5. **The owner's runs are counted.** Each run that gets as far as computing signals is a trial
   of its algorithm (a run that stops on a syntax error is not); the count is shown beside every
   result, because a result found after many tries is weaker than the same result found first.
6. **Separate from the research record.** Algorithms and their runs live in the Lab folder
   (`KINN_LAB_DIR`, default `lab/` beside the run store), outside git and outside the run
   store, so the agents' record and trial counts are untouched. Each run keeps a copy of the
   code and settings it ran, with their hash, so any result can be reproduced. An idea that
   holds up becomes a strategy (`docs/NEW_STRATEGY.md`) and goes through the usual protocol.
7. **Run in a separate process.** The Workbench server starts a worker process per run
   (`python -m kinn.lab.worker`), which writes its progress and results to the run's folder. A
   crash or an endless loop in the owner's code cannot stop the Workbench, and a run can be
   cancelled. One run at a time.
8. **Only the Workbench's own page can start a run.** The server listens on 127.0.0.1 only.
   Requests that change anything must carry a session token that only a page served by the
   Workbench can read, and must name the Workbench as their host and origin (the Host check
   also stops DNS rebinding). A web page elsewhere cannot make the server run code. Started
   with `--host` beyond this machine, the Workbench turns the Lab off.

**Consequences.** The Workbench, until now read-only, can start a process that runs code; the
README and AGENTS.md say so. The Lab adds pandas as a dependency (the language owners write
research code in). A run over 2005–2023 and every stock needs several gigabytes of memory on
the Mac (about 2 GB for a $50M-and-up universe, before the code's own tables); the Lab refuses a
run that would need more than 60% of the machine's memory, with the size in the message. The
data the code gets is shared and read-only underneath; pandas copies a table on the code's
first change to it. The default period is 2010–2017 (the search years), and the Lab offers the
test periods separately so the owner can hold them back as the agents do.

**Deferred (recorded, not built):** minute-bar fields; news, short interest and short volume
fields (Massive files on disk from 2016 only, read outside the store today); parameter sweeps;
a factor (rank-decile) report; several runs at once.

**Added the same day, after the owner's first run failed** (a field clicked in the Data tab was
written at the top of his file, and the syntax error was shown where he could not see it):

9. **The code is checked before it runs, without running it** (`kinn.lab.check`, `ast` only):
   errors (syntax, no `signal(data)`, a refused `SETTINGS`) block the Run button and are refused
   by the server; warnings (an unknown `data.` field with the nearest one named, a negative
   shift, a centered window, a missing helper module) are marked on the line as he types.
10. **Nothing is written into the code at a place he cannot see:** a field is inserted only at
    a cursor he has placed, and copied otherwise. The toolbar shows how the last run ended, and
    the page moves to the results when a run he started ends.
11. **A run has a time limit** (30 minutes by default) that the code's own `except Exception`
    cannot catch, a log line a stage with the time, and the time each stage took.
12. **Helper modules** (`lab/library/<name>.py`, imported as `lab.<name>`) let algorithms share
    code; each run keeps a copy of the library and its hash, so an old result never changes.
13. **A cache of loaded fields between runs** (memory-mapped files keyed by data build,
    universe and window; 6 GB at most, least recently used dropped first).
14. **The command line** (`kinn lab list | run | selfcheck`) runs through the same runner and
    folder, so a run from the terminal is counted and shown like one from the page.
15. **Nothing but typing writes into the code** (the same evening: a field clicked in the Data
    tab still went in at a remembered cursor and replaced a selection, wiping an algorithm that
    was then saved). The Data tab is a reference with copy buttons, and **every save keeps the
    version before it** (`lab/history/`, the last 200 a file), restorable from a History tab:
    no click or save can lose code again.
