"""A Screener screen as a Lab algorithm: the same filters, tested on every session with what
was known that morning or the evening before, instead of on one day's list."""

from __future__ import annotations

import json
import re
import textwrap
from urllib.parse import parse_qs

FIELDS: dict[str, tuple[str, str, str]] = {
    "close": ("price", "data.close", "price"),
    "market_cap": ("money", "data.market_cap", "market_value"),
    "adv20": ("money", "data.adv20", "dollar_volume"),
    "ret_1d": ("percent", "price / price.shift(1) - 1", "return_1d"),
    "ret_1m": ("percent", "price / price.shift(21) - 1", "return_1m"),
    "ret_3m": ("percent", "price / price.shift(63) - 1", "return_3m"),
    "ret_6m": ("percent", "price / price.shift(126) - 1", "return_6m"),
    "ret_1y": ("percent", "price / price.shift(252) - 1", "return_1y"),
    "from_high": ("percent", "price / (data.high * price / data.close).rolling(252).max() - 1",
                  "from_high"),
    "vol_60": ("percent", "data.returns.rolling(60).std() * 252**0.5", "volatility"),
    "pe": ("ratio", "data.market_cap / data.net_income.where(data.net_income > 0)", "pe"),
    "ps": ("ratio", "data.market_cap / data.revenue.where(data.revenue > 0)", "ps"),
    "pb": ("ratio", "data.market_cap / data.equity.where(data.equity > 0)", "pb"),
    "fcf_yield": ("percent", "data.free_cash_flow / data.market_cap", "fcf_yield"),
    "revenue": ("money", "data.revenue", "revenue"),
    "revenue_growth": ("percent", "data.revenue / data.revenue.shift(252).where("
                       "data.revenue.shift(252) > 0) - 1", "revenue_growth"),
    "net_income": ("money", "data.net_income", "net_income"),
}  # fmt: skip
SCALE = {"k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12}
STATIC = ("sector", "industry", "exchange")
HOLD = 21


class ScreenError(ValueError):
    """A screen the Lab cannot turn into an algorithm; the message says why."""


def value(text: str, kind: str) -> float | None:
    clean = re.sub(r"[$,%\s]", "", text.strip()).replace("−", "-").lower()
    if not clean:
        return None
    match = re.fullmatch(r"(-?\d*\.?\d+)([kmbt])?", clean)
    if not match or (match.group(2) and kind != "money"):
        raise ScreenError(f"{text!r} is not a number.")
    number = float(match.group(1)) * (SCALE[match.group(2)] if match.group(2) else 1.0)
    return number / 100 if kind == "percent" else number


def literal(number: float) -> str:
    if number == int(number) and abs(number) >= 1e5:
        return f"{number:.6g}".replace("e+0", "e").replace("e+", "e")
    return repr(number)


def algorithm(query: str, title: str) -> str:
    params = parse_qs(query, keep_blank_values=True)
    lines: list[str] = []
    used: list[str] = []
    for part in params.get("f", []):
        field, low, high = ([*part.split(":"), "", ""])[:3]
        if field not in FIELDS:
            raise ScreenError(f"The Lab has no field for {field!r}.")
        kind, expression, name = FIELDS[field]
        bounds = [(">=", value(low, kind)), ("<=", value(high, kind))]
        tests = [f"({name} {op} {literal(number)})" for op, number in bounds if number is not None]
        if not tests:
            continue
        if name not in used:
            lines.append(f"    {name} = {expression}")
            used.append(name)
        lines.append(f"    passes &= {' & '.join(tests)}")
    for key in STATIC:
        chosen = (params.get(key) or [""])[0]
        if chosen:
            lines.append(f"    passes &= data.{key} == {json.dumps(chosen)}")
    if not lines:
        raise ScreenError("The screen has no filter the Lab can test. Add a range or a sector.")
    left_out = [w for w, k in (("text search", "q"), ("kind of stock", "kind")) if params.get(k)]
    note = ""
    if left_out:
        verb = "are" if len(left_out) > 1 else "is"
        note = f" Its {' and '.join(left_out)} {verb} left to the universe settings."
    sentence = (f"{title}, from the Screener, as a rule on every session: a stock is bought at "
                f"the next open on a day it passes and held {HOLD} sessions.{note}")  # fmt: skip
    doc = '"""' + "\n".join(textwrap.wrap(sentence, 96)) + '"""'
    body = "\n".join(lines)
    return (f"{doc}\n\nSETTINGS = {{\"exit\": {{\"hold_days\": {HOLD}}}}}\n\n\n"
            f"def signal(data):\n    price = data.adj_close\n    passes = data.close > 0\n"
            f"{body}\n    return passes\n")  # fmt: skip


def name_for(title: str, taken: set[str]) -> str:
    stem = re.sub(r"[^a-z0-9]+", "_", f"screen {title}".lower()).strip("_")[:56] or "screen"
    name, n = stem, 2
    while name in taken:
        name, n = f"{stem}_{n}", n + 1
    return name
