# AGENTS.md — rules for every AI agent working on Kinn

Kinn is a research platform for finding, validating and (later) paper-trading intraday equity
strategies. One person owns it; AI agents (Claude, GPT) do much of the coding, sometimes at the
same time. These rules keep the research honest and the agents out of each other's way.
Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Why: [docs/decisions/](docs/decisions/).

## Repo map

| Path | What | May import |
|---|---|---|
| `src/kinn/` | The platform: stable, tested, shared | nothing outside itself |
| `src/kinn/core` | Types, calendar, settings | nothing else in `kinn` |
| `src/kinn/data` | Ingestion, security master, point-in-time universes, holdout seal, audit | |
| `src/kinn/features` | Features; each declares when its value is available | |
| `src/kinn/costs` | `CostModel` + `calibrations/*.yaml` | |
| `src/kinn/risk` | Sizing, exposure and buying-power limits | |
| `src/kinn/engine/intraday` | Event-driven minute simulator, fill models | |
| `src/kinn/validation` | Walk-forward, purged CV, DSR, PBO, permutation, canaries | |
| `src/kinn/registry` | Run manifests + DuckDB index | |
| `src/kinn/reporting` | Standard tearsheet | |
| `strategies/<name>/` | One strategy: universe, signals, parameters. Nothing else | `kinn` |
| `apps/workbench/` | Research UI; reads only the run store through the schemas | `kinn` |
| `research/<agent>/` | Sandbox. Never imported, never a source of results | anything |
| `tests/` | Unit, canary, regression | |
| `docs/` | Architecture, owners, salvage log, decisions, retired strategies, checkpoints | |

Outside the repo, beside it: `runs/` (run outputs, `KINN_RUNS_DIR`) and one git worktree per agent.

## Import rules (enforced by import-linter, in pre-commit and in the tests)

1. `strategies/` and `apps/` may import `kinn`. `kinn` never imports them.
2. Nothing imports `research/`.
3. `apps/` never imports `strategies/`.
4. `kinn.core` imports no other part of `kinn`.

The old package under `~/Desktop/QTS` is legacy. Never import it, install it, or use its name as
an identifier (a test checks). It is reference material only, under the salvage protocol.

## How to work

```bash
uv sync                      # one locked environment
uv run pre-commit install    # once per clone or worktree
uv run pytest                # unit tests, canaries, repo rules
uv run lint-imports          # import rules
uv run ruff check . && uv run ruff format .
uv run kinn paths            # where Kinn reads and writes
```

Runs (from Phase 2): `uv run kinn run <strategy> --config <name>`. This is the only entry point.

- Each run writes `runs/<run_id>/` with `manifest.json`, trades, equity and metrics.
- `run_id = <UTC timestamp>_<agent>_<strategy>_<short hash>`. Set `KINN_AGENT` to `claude` or `gpt`.
- A run from code with uncommitted changes is refused unless tagged `--scratch`. Scratch runs
  are excluded from reports. Commit first, then run.
- Every run is a trial. Trial counts for Deflated Sharpe and PBO cover every run by every agent
  in the strategy family. Never delete a run folder to make a count smaller.

## Lanes

- Before editing, check [docs/OWNERS.md](docs/OWNERS.md). One owner per platform module at a time.
- Claim a lane in your pull request by editing `docs/OWNERS.md` in the same PR.
- A change to a module you don't own goes to `docs/requests/` as a short note, not as code.
- Work only in your own worktree, on a branch named `agent/<claude|gpt>/<task>`.
- Never commit to `main` (a pre-commit hook refuses it).

## Bias checklist: go through it before trusting any number

1. **Feature availability.** Every feature declares when its value is known. The engine refuses
   earlier use. Never work around the refusal.
2. **Next-bar execution.** A signal from bar *t* acts at the open of bar *t+1* or later.
3. **Point-in-time universes.** Membership on a date uses only what was known on that date.
4. **Survivorship.** Delisted names are in the universe until they delist.
5. **Holdout seal.** No date on or after 2023-11-09, from any source, in any build step.
6. **Trial counting.** Every run counts, including the ones that failed.
7. **Costs at 1× and 2× slippage.** A result that dies at 2× is reported as fragile.

## Research discipline

- Write `HYPOTHESIS.md` before the first test: rationale, universe, event definition, risks.
- Log every run through `kinn run`. A number that is not in the run store does not exist.
- End every strategy with a `REPORT.md` that gives a verdict: develop, park or retire.
- Write for the owner: plain statements, the number, and what would change your mind.

## Human-only actions: never do these, ask the owner

- Merging to `main`.
- Unsealing the holdout (`--unseal` with `KINN_UNSEAL_TOKEN`). Never read, list or unlock
  `MarketData/sealed/`, even if your session can reach it.
- Anything that writes to, moves or re-downloads raw data (`KINN_RAW_DIR`).
- Reading, printing, copying or committing `.env` files or keys, old or new.
- Broker settings and live trading. Live trading is locked; paper comes first.

## Salvage

Old code is for ideas. A piece enters Kinn only if you (a) understand it and rewrite it to the
new interfaces, (b) it passes the new tests including the lookahead canaries, and (c) you log it
in [docs/SALVAGE.md](docs/SALVAGE.md): what, from where, what changed, why it is trustworthy.
No bulk copying. The same protocol covers `research/external/` deliveries.

## Keep it small

One person, one active strategy. No plugin registries, services, queues or frameworks "for
later". When in doubt, write the simpler version and record the deferral in `docs/decisions/`.
Never commit secrets, data or run outputs; pre-commit blocks them, and so should you.
