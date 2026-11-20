"""What a trade costs under the platform's cost model (decision 0004), as the Lab charges it:
an auction fill pays the auction allowance, a marketable fill the half-spread; 2× doubles the
slippage. Read-only arithmetic over ``kinn.costs``."""

from __future__ import annotations

from datetime import timedelta

from apps.workbench import stocks
from kinn.costs.model import CostModel, load

MODEL = "ibkr_pro_tiered"
SIZES = (500, 1_000, 2_000, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000)
PRICES = (1, 2, 3, 5, 10, 20, 50, 100, 250)
FILLS = ("auction", "marketable")


class CostError(ValueError):
    """An input the calculator cannot use; the message names it."""


def _number(raw: str | None, name: str, *, low: float, high: float, optional: bool = False):
    if raw in (None, ""):
        if optional:
            return None
        raise CostError(f"{name} is required.")
    try:
        value = float(raw)
    except ValueError:
        raise CostError(f"{name} must be a number.") from None
    if not low <= value <= high:
        raise CostError(f"{name} must be from {low:g} to {high:g}.")
    return value


def order(model: CostModel, *, side: str, price: float, value: float, adv: float | None,
          fill: str) -> dict:  # fmt: skip
    shares = max(int(round(value / price)), 1)
    value = shares * price
    auction = fill == "auction"
    commission, fees = model.order_fees(side=side, value=value, marketable=0 if auction else shares,
                                        passive=0, auction=shares if auction else 0)  # fmt: skip
    if auction:
        slippage = model.auction_slippage(price=price, shares=shares)
    else:
        slippage = model.half_spread_bps(price, adv) / 1e4 * value
    return {"side": side, "fill": fill, "shares": shares, "value": value,
            "commission": commission, "fees": fees, "slippage": slippage}  # fmt: skip


def round_trip(model: CostModel, *, price: float, value: float, adv: float | None,
               entry: str = "auction", exit_: str = "auction",
               short: bool = False) -> dict:  # fmt: skip
    opening, closing = ("sell", "buy") if short else ("buy", "sell")
    legs = [order(model, side=opening, price=price, value=value, adv=adv, fill=entry),
            order(model, side=closing, price=price, value=value, adv=adv, fill=exit_)]  # fmt: skip
    cost = sum(leg["commission"] + leg["fees"] + leg["slippage"] for leg in legs)
    slippage = sum(leg["slippage"] for leg in legs)
    size = legs[0]["value"]
    return {"legs": legs, "cost": cost, "cost_2x": cost + slippage,
            "bps": cost / size * 1e4, "bps_2x": (cost + slippage) / size * 1e4}  # fmt: skip


def estimate(query: dict[str, str]) -> dict:
    price = _number(query.get("price"), "Price", low=0.01, high=100_000)
    value = _number(query.get("value"), "Position", low=10, high=100_000_000)
    adv = _number(query.get("adv"), "Average daily dollar volume", low=0, high=1e12, optional=True)
    entry, exit_ = query.get("entry") or "auction", query.get("exit") or "auction"
    if entry not in FILLS or exit_ not in FILLS:
        raise CostError("A fill is 'auction' or 'marketable'.")
    short = query.get("side") == "short"
    model = load(MODEL)
    trip = lambda p, v: round_trip(model, price=p, value=v, adv=adv, entry=entry,  # noqa: E731
                                   exit_=exit_, short=short)  # fmt: skip
    out = trip(price, value)
    return {
        **out, "model": model.name, "price": price, "adv": adv,
        "half_spread_bps": model.half_spread_bps(price, adv),
        "auction_bps": model.auction_bps,
        "sizes": [{"value": v, **{k: trip(price, v)[k] for k in ("bps", "bps_2x")}} for v in SIZES],
        "prices": [{"price": p, **{k: trip(p, value)[k] for k in ("bps", "bps_2x")}}
                   for p in PRICES],
    }  # fmt: skip


def quote(store: stocks.Store, symbol: str) -> dict | None:
    """A stock's last close and 20-day average dollar volume before the seal."""
    found = stocks.resolve(store, symbol)
    if not found:
        return None
    perm = found[0]
    company = stocks.index(store).companies[perm]
    end = min(stocks._day(company.get("last_price_date")) or stocks.LAST, stocks.LAST)
    rows = []
    for start in (end - timedelta(days=40), stocks.FIRST):
        rows = [r for r in store.panel_of(start, end, permatickers=[perm],
                                          columns="date, symbol, close, adv20_prev").to_pylist()
                if r["close"]]  # fmt: skip
        if rows:
            break
    if not rows:
        return None
    row = rows[-1]
    return {"ticker": company.get("ticker") or symbol.upper(), "name": company.get("name"),
            "date": row["date"].isoformat(), "price": row["close"],
            "adv": row["adv20_prev"]}  # fmt: skip
