# 0011 — Workbench: one static page and a standard-library server

**Status:** taken by claude in Phase 4, 2026-11-15. Over-engineering guard.

**Decision.** `apps/workbench` is a single HTML page with plain JavaScript and CSS, served by a
small `http.server` that exposes three read-only JSON endpoints over the run store. No React,
no Node toolchain, no database: the run folders are the database.

**Why.** One user, read-only views, a few dozen runs. A build chain would be the largest
dependency in the repo and nothing here needs it.

**Revisit when** the Workbench must launch runs, or the page outgrows one file (roughly 1,000
lines of JavaScript), or run counts make reading manifests on every request slow (then serve
from the registry's DuckDB index).
