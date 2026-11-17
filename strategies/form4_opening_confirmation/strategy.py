"""Buy a confirmed opening advance following a public Form 4 purchase."""

from datetime import date
from math import isfinite

import numpy as np

from kinn.core.types import Disclosure, Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


def has_material_purchase(filings: tuple[Disclosure, ...], day: date) -> bool:
    issuers = set()
    amounts = {}
    for filing in filings:
        amount = filing.purchase_amount
        if (
            filing.filed >= day
            or filing.document_type != "4"
            or filing.transaction_code != "P"
            or filing.acquired != "A"
            or amount is None
            or not isfinite(amount)
            or amount <= 0
        ):
            continue
        if not filing.issuer_cik or not filing.accession:
            return False
        issuers.add(filing.issuer_cik)
        if amounts.setdefault(filing.accession, amount) != amount:
            return False
    return len(issuers) == 1 and sum(amounts.values()) >= 100_000


def confirms_opening(view: DayView, bars: SymbolDay, adv: float) -> bool:
    opening = int(bars.minute.searchsorted(view.open_minute))
    decision = view.open_minute + 14
    end = int(bars.minute.searchsorted(decision))
    if end <= opening or end >= len(bars.minute):
        return False
    if (
        bars.minute[opening] != view.open_minute
        or bars.minute[end - 1] != decision - 1
        or bars.minute[end] != decision
    ):
        return False
    price = bars.open[opening]
    last_closes = bars.close[end - 1 : end + 1]
    if (
        not isfinite(price)
        or price <= 0
        or not (np.isfinite(last_closes) & (last_closes >= 1.02 * price)).all()
    ):
        return False
    close = bars.close[opening : end + 1]
    volume = bars.volume[opening : end + 1]
    turnover = np.zeros(len(close))
    np.multiply(close, volume, out=turnover, where=np.isfinite(close) & (close > 0))
    return turnover[-1] >= 40_000 and turnover.sum() >= 0.10 * adv


class Form4OpeningConfirmation:
    name = "form4_opening_confirmation"
    universe = Universe(
        name, min_prev_close=2, min_adv20=1e6, min_marketcap=50e6, max_marketcap=2e9
    )
    features = (f.ADV20,)
    inputs = {"form4": {"sessions": 1}}

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        decision = view.open_minute + 14
        found = []
        for symbol, filings in view.disclosures.items():
            if not has_material_purchase(filings, view.day):
                continue
            if confirms_opening(view, view.symbols[symbol], features[symbol][f.ADV20.name]):
                found.append(Signal(symbol, decision, expire_minute=decision + 1))
        return found


def build(params: dict) -> Form4OpeningConfirmation:
    if params:
        raise ValueError("form4_opening_confirmation accepts no parameters")
    return Form4OpeningConfirmation()
