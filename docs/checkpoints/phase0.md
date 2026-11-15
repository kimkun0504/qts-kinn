# Checkpoint: Phase 0 (foundation), 2026-11-15

**Done.** Repo skeleton, one locked `uv` environment (Python 3.13), settings, pre-commit
(gitleaks, large-file block, data/.env block, no-commit-to-main, ruff, import-linter), AGENTS.md,
CLAUDE.md, ARCHITECTURE.md, eight decision records, three retired/prior-work pages.
13 tests pass; 4 import contracts kept; gitleaks finds nothing.

**The owner said on 2026-11-15 to continue through the phases without waiting at checkpoints.**
The objections below are therefore handled with the stated default until the owner says otherwise.

## Objections and open decisions

| # | Issue | Default taken | Owner decision needed? |
|---|---|---|---|
| 1 | **`sealed/` is reachable from the agent session.** The connected folder is all of `~/Desktop/QTS`, which contains `MarketData/sealed/`, and its permissions do not block the agent. The "physical" layer of the seal is not in effect. | Not listed, read or opened. Settings refuse any path containing `sealed`. | **Yes.** Connect only `MarketData/raw`, `MarketData/processed` and the Kinn folder to agent sessions, or move `sealed/` outside `~/Desktop/QTS`. |
| 2 | **The research window is already used up for this hypothesis.** The earlier rebound build ran 6 pre-registered trials and tabulated about 2,300 variants on 2003–2023 (docs/retired/intraday-rebound-v0.md). A "from scratch" HYPOTHESIS.md cannot un-see that. | The `intraday_rebound` family inherits the prior looks. Phase 3's event study is described as a replication on a new engine, not as fresh evidence. | **Yes:** how many trials the exploration counts as (proposal: its 3 logged looks plus the effective number of independent variants, estimated in Phase 2's PBO code). |
| 3 | **3–4% net a trade conflicts with what is already known.** Only one rule reached it, in the thinnest micro caps, with resting orders, and it fell to about +2% (or ~0 under the harshest exit) once fills were priced conservatively. Minute bars have no quotes, so queue position cannot be resolved by this data. | Trade-through margin, auction participation and exit price are engine settings shown in every report. The target is tested, not forced. | Later: buy a quote/tick sample before believing any limit-order result. |
| 4 | **NEW_ROOT was not filled in.** | Took `~/Desktop/QTS/qts-kinn/` (the empty folder created today) as NEW_ROOT, so the repo is `~/Desktop/QTS/qts-kinn/qts-kinn/`, with `runs/` and worktrees beside it. | Only if you want it elsewhere; moving is one `mv`. |
| 5 | **Agent shell cannot delete files in your folders**, which git needs. Granting deletion applies to all of `~/Desktop/QTS`, including raw data. | Not requested. The repo is built in the agent's scratch space and copied to your folder after each commit. | Same fix as #1: connect the Kinn folder on its own; then deletion can be granted for it alone. |
| 6 | **Commit attribution.** The old repos used "Kun Kim, no AI trailers". Kinn wants to know which agent did what. | Commits are authored as Kun Kim without trailers; the branch name (`agent/claude/...`) and run manifests carry the agent. | Say if you want `Co-Authored-By` trailers instead. |
| 7 | **gitleaks pre-commit hook builds with Go** on first use (downloads a Go toolchain). | Kept the standard hook. In the agent VM the download is blocked, so the gitleaks binary is run directly. | No. |
| 8 | **Parameter heatmaps in the Workbench (Phase 4) have nothing to show**, because Phase 3 forbids a parameter search. | The view is built against the schema with canary/random-signal sweeps as test data. | No. |
| 9 | **"Random entries must lose money after costs"** is true on average, not for every seed. | The canary tests the mean net return over many random entries with a confidence bound and a fixed seed. | No. |
| 10 | **`main` does not exist yet.** Agents may not commit to it. | Phase 0 is on `agent/claude/phase0-foundation`. | Create `main` from it (on GitHub: set it as the base, or `git branch main agent/claude/phase0-foundation`). |

## Not built in Phase 0, on purpose

`kinn run` (Phase 2), any strategy code, `strategies/_template/strategy.py` (waits for the
strategy interface), internal layer contracts beyond `kinn.core` (wait for the modules).
