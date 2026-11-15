"""Point-in-time universes: filters on the daily panel that use only pre-open information."""

from __future__ import annotations

from dataclasses import dataclass

COMMON_STOCK = (
    "Domestic Common Stock",
    "Domestic Common Stock Primary Class",
    "Domestic Common Stock Secondary Class",
)

# The only panel columns a universe may filter on: known before the open of `date`.
PRE_OPEN_COLUMNS = ("prev_close", "adv20_prev", "marketcap_prev", "sessions_prior", "category")


@dataclass(frozen=True)
class Universe:
    """Membership on ``date`` is decided from the prior sessions only.

    Money amounts are in dollars. ``None`` means no bound. Bounds are inclusive below and
    exclusive above, so adjacent universes do not overlap.
    """

    name: str
    categories: tuple[str, ...] = COMMON_STOCK
    min_prev_close: float | None = None
    max_prev_close: float | None = None
    min_adv20: float | None = None
    max_adv20: float | None = None
    min_marketcap: float | None = None
    max_marketcap: float | None = None
    min_sessions_prior: int = 20

    def where(self) -> str:
        """A SQL predicate over panel columns."""
        quoted = ", ".join("'" + c.replace("'", "''") + "'" for c in self.categories)
        clauses = [f"category in ({quoted})", f"sessions_prior >= {int(self.min_sessions_prior)}"]
        for column, low, high in (
            ("prev_close", self.min_prev_close, self.max_prev_close),
            ("adv20_prev", self.min_adv20, self.max_adv20),
            ("marketcap_prev", self.min_marketcap, self.max_marketcap),
        ):
            if low is not None:
                clauses.append(f"{column} >= {float(low)!r}")
            if high is not None:
                clauses.append(f"{column} < {float(high)!r}")
        return " and ".join(clauses)
