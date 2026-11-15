"""Random entries: the canary that must lose money after costs.

Each session it picks a few universe members and a minute for each, using a random generator
seeded by the date. Nothing depends on the day's prices, so there is no edge by construction.
"""

from __future__ import annotations

import random

from kinn.core.types import Signal
from kinn.data.universe import Universe


class RandomEntry:
    name = "random_entry"
    features = ()

    def __init__(self, params: dict):
        self.entries = int(params.get("entries_per_session", 10))
        self.hold = int(params.get("hold_minutes", 60))
        self.seed = int(params.get("seed", 0))
        self.universe = Universe(
            "random_entry",
            min_prev_close=float(params.get("min_price", 5.0)),
            min_adv20=float(params.get("min_adv", 2_000_000.0)),
            min_sessions_prior=int(params.get("min_sessions_prior", 20)),
        )

    def signals(self, view, features):
        rng = random.Random(f"{self.seed}:{view.day.isoformat()}")
        names = sorted(view.symbols)
        chosen = rng.sample(names, min(self.entries, len(names)))
        last = view.close_minute - 30
        return [
            Signal(s, rng.randrange(view.open_minute, last), max_hold_minutes=self.hold)
            for s in chosen
        ]


def build(params: dict) -> RandomEntry:
    return RandomEntry(params)
