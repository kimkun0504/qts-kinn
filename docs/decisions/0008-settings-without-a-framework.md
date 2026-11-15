# 0008 — Settings: a frozen dataclass read from the environment

**Status:** accepted, 2026-11-15 (claude, Phase 0). Over-engineering guard.

**Decision.** `kinn.core.settings` is a small frozen dataclass filled from `KINN_*` variables,
with no settings library and no `.env` loading. Three paths today.

**Deferred.** `.env` loading and a settings library, until there are secrets or enough settings
to need them. The owner creates any `.env`; agents never read one.
