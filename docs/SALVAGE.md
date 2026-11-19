# Salvage log

Old code (`~/Desktop/QTS/*`, read-only) and external deliveries (`research/external/`) are sources
of ideas, not of code. A piece enters Kinn only if:

- (a) the agent understands it and rewrites it to the new interfaces;
- (b) it passes the new tests, including the lookahead canaries;
- (c) it is recorded below.

No bulk copying. Ideas and lessons (as opposed to code) are recorded in `docs/retired/`.

| Date | What was taken | From (repo, path, commit) | What changed | Why it is trustworthy | Agent |
|---|---|---|---|---|---|
| 2026-11-19 | Complete price-candidate quote planning | Kinn `research/gpt/plan_bid_quote_windows.py`, `e08de30` / `9d6b83c` | Rewritten as native pure window construction, strict source validation and runner-level price-only enumeration. No sandbox import; no forward outcomes. | Native source/hash, immutable-plan, exact-time/DST, replay, post-decision perturbation and runner pinning tests; full platform checks recorded with the adapter. | gpt |
