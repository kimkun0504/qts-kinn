"""Position sizing and buying-power limits.

Sizing is fixed-dollar against a fixed account size (decision 0003: size as if only the
starting allocation exists). Because the engine is flat every night and sizes never depend on
earlier profits, each session can be simulated on its own.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    equity: float = 10_000.0
    position_dollars: float = 500.0
    buying_power: float = 10_000.0  # cap on open positions plus resting entry orders
    max_positions: int | None = None  # open positions plus resting entry orders
    max_entries_per_session: int | None = None  # filled entries a session
    daily_loss_limit: float | None = (
        None  # dollars; no new entries once the session is down this much
    )

    def shares(self, weight: float, reference_price: float) -> int:
        """Whole shares for one position; zero if one share costs more than the position."""
        if reference_price <= 0 or weight <= 0:
            return 0
        return int(self.position_dollars * weight / reference_price)


class BuyingPower:
    """Tracks reservations over the session. A resting entry order reserves capital too."""

    def __init__(self, config: RiskConfig):
        self._config = config
        self._active: list[tuple[int, float, str]] = []  # (release minute, dollars, symbol)

    def try_reserve(self, *, symbol: str, start: int, release: int, dollars: float) -> bool:
        self._active = [r for r in self._active if r[0] > start]
        if any(r[2] == symbol for r in self._active):
            return False  # one position or order per symbol at a time
        if (
            self._config.max_positions is not None
            and len(self._active) >= self._config.max_positions
        ):
            return False
        if sum(r[1] for r in self._active) + dollars > self._config.buying_power + 1e-9:
            return False
        self._active.append((release, dollars, symbol))
        return True
