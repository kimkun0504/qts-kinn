# 0013 — Workbench rebuilt in React, TypeScript, Tailwind and Vite

**Status:** accepted, 2026-11-15 (owner). Supersedes 0011.

**Context.** The first Workbench was one static page with hand-written CSS. The owner judged its
look unacceptable and asked for a dashboard in the style of institutional brokerage tools, with a
side rail, built on React, TypeScript, Tailwind and Vite with component-based styling.

**Decision.** `apps/workbench/web` is a Vite project. The Python server and its three read-only
endpoints are unchanged; the server now serves `web/dist`. Styling is held in a small set of UI
components over design tokens; pages do not carry their own styling beyond layout. Charts are
hand-drawn SVG components (two chart types do not justify a chart library yet).

**Consequences.** The repo gains a Node toolchain (Node 22, `npm`), a second CI job, and a build
step before the Workbench can be opened. Still deferred: launching runs from the UI.
