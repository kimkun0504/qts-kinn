"""Buy an intraday recovery below a newly disclosed insider purchase reference."""

from math import isfinite

from kinn.core.types import Disclosure, Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import PREV_CLOSE


def purchase_reference(view: DayView, symbol: str, filings: tuple[Disclosure, ...]) -> float | None:
    purchases: dict[str, tuple[float, float]] = {}
    issuers = set()
    for filing in filings:
        amount = filing.purchase_amount
        shares = filing.shares
        if (
            filing.filed >= view.day
            or filing.symbol != symbol
            or filing.document_type != "4"
            or filing.transaction_code != "P"
            or filing.acquired != "A"
            or not (filing.officer or filing.director)
            or not filing.accession
            or not filing.issuer_cik
            or amount is None
            or not isfinite(amount)
            or amount < 100_000
            or shares is None
            or not isfinite(shares)
            or shares <= 0
        ):
            continue
        purchase = (amount, shares)
        if purchases.setdefault(filing.accession, purchase) != purchase:
            return None
        issuers.add(filing.issuer_cik)

    if len(issuers) != 1:
        return None
    accession = min(purchases, key=lambda key: (-purchases[key][0], key))
    amount, shares = purchases[accession]
    price = amount / shares
    return price if isfinite(price) and price > 0 else None


def reclaim_minute(
    view: DayView, bars: SymbolDay, prior_close: float, reference: float
) -> int | None:
    reclaim = 0.955 * reference
    ceiling = 1.10 * reference
    if not reclaim <= prior_close <= ceiling:
        return None

    opening = int(bars.minute.searchsorted(view.open_minute))
    if (
        opening == len(bars.minute)
        or bars.minute[opening] != view.open_minute
        or not reclaim <= bars.open[opening] <= ceiling
    ):
        return None

    earliest = view.open_minute + 5
    latest = min(13 * 60, view.close_minute - 15)
    last = int(bars.minute.searchsorted(latest, side="right"))
    washout = 0.94 * reference
    max_entry_close = 0.97 * reference
    washed_out = 0 < bars.close[opening] <= washout
    for i in range(opening + 1, last):
        close = bars.close[i]
        minute = int(bars.minute[i])
        if (
            washed_out
            and minute >= earliest
            and reclaim <= close <= max_entry_close
            and bars.minute[i - 1] == minute - 1
            and 0 < bars.close[i - 1] < reclaim
            and close * bars.volume[i] >= 40_000
        ):
            return minute
        washed_out = washed_out or 0 < close <= washout
    return None


class InsiderPriceReclaim:
    name = "insider_price_reclaim"
    universe = Universe(
        name, min_prev_close=2, min_adv20=1e6, min_marketcap=50e6, max_marketcap=2e9
    )
    features = (PREV_CLOSE,)
    inputs = {"form4": {"sessions": 1}}

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, filings in view.disclosures.items():
            reference = purchase_reference(view, symbol, filings)
            if reference is None:
                continue
            bars = view.symbols[symbol]
            minute = reclaim_minute(view, bars, features[symbol][PREV_CLOSE.name], reference)
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1))
        return found


def build(params: dict) -> InsiderPriceReclaim:
    if params:
        raise ValueError("insider_price_reclaim accepts no parameters")
    return InsiderPriceReclaim()
