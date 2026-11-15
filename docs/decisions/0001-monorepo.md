# 0001 — One monorepo, one locked environment

**Status:** accepted, 2026-11-15 (owner).

**Context.** The earlier build spread over several repos, each with its own package, environment
and partial copy of the data loaders and cost model. Results stopped being comparable.

**Decision.** One git repo (`qts-kinn`), one Python package (`kinn`), one `uv.lock`. Strategies,
apps and sandbox live in the same repo, separated by import rules, not by repos.

**Consequences.** One cost model and one simulator for every strategy. Agents separate their work
with worktrees and lanes (docs/OWNERS.md) instead of repos.
