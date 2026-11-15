"""<name>: one sentence. The definition is fixed in HYPOTHESIS.md.

A strategy is thin: a universe, the features it reads, and a function from one session's view
to signals. It must not load data, model costs or simulate fills.
"""

from __future__ import annotations

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.features import library as f


class Template:
    name = "_template"
    features = (f.RETURN_FROM_PREV_CLOSE, f.PREV_CLOSE)

    def __init__(self, params: dict):
        self.threshold = float(params["threshold"])
        self.universe = Universe("template", min_prev_close=5.0, min_adv20=1_000_000.0)

    def signals(self, view, features):
        out = []
        for symbol, sd in view.symbols.items():
            values = features[symbol]["return_from_prev_close"]
            hits = (values <= -self.threshold).nonzero()[0]
            if len(hits):
                # `minute` is the last bar the decision used; the order is live from the next bar.
                out.append(Signal(symbol, int(sd.minute[hits[0]]), max_hold_minutes=60))
        return out


def build(params: dict) -> Template:
    return Template(params)
