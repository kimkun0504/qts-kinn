"""The settings of a Lab run: period, universe, entry, exit, book. One place, validated."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date

from kinn.data.seal import HOLDOUT_START

# The last day a position may be opened in each period. Exits may run on to the day before the
# seal (2023-11-08), so the last entries of 2023 have room for a 20-session hold.
LAST_ENTRY = date(2023, 10, 13)
PERIODS: dict[str, tuple[date, date, str]] = {
    "search": (date(2010, 1, 1), date(2017, 12, 31), "2010–2017 (search years)"),
    "early": (date(2005, 1, 1), date(2009, 12, 31), "2005–2009 (test years)"),
    "late": (date(2018, 1, 1), date(2022, 12, 31), "2018–2022 (test years)"),
    "check": (date(2023, 1, 1), LAST_ENTRY, "2023 to 13 October (check)"),
    "all": (date(2005, 1, 1), LAST_ENTRY, "2005 to 13 October 2023"),
}
FIRST_DAY = date(2004, 1, 2)
MAX_HOLD = 250


class SettingsError(ValueError):
    """A setting is missing, of the wrong kind or out of range. The message names it."""


@dataclass
class Universe:
    min_market_cap: float = 50e6
    max_market_cap: float | None = None
    min_price: float = 2.0
    min_dollar_volume: float = 250_000.0
    exclude_blank_checks: bool = False


@dataclass
class Entry:
    mode: str = "signal"  # "signal": every True; "rank": the top N scores each day
    top_n: int = 10
    rank_order: str = "highest"  # "highest" or "lowest" scores first


@dataclass
class Exit:
    hold_days: int = 20
    stop_loss: float | None = None  # 0.10: sell if the price falls 10% below the entry
    take_profit: float | None = None  # 0.25: sell if the price rises 25% above the entry


@dataclass
class Book:
    position_size: float = 2_000.0
    max_positions: int = 20  # 0: no limit


@dataclass
class Settings:
    period: str = "search"
    start: date | None = None  # only for period "custom"
    end: date | None = None
    universe: Universe = field(default_factory=Universe)
    entry: Entry = field(default_factory=Entry)
    exit: Exit = field(default_factory=Exit)
    book: Book = field(default_factory=Book)

    def window(self) -> tuple[date, date]:
        """(first day a signal may fire, last day a position may open)."""
        if self.period == "custom":
            assert self.start is not None and self.end is not None
            return self.start, self.end
        start, end, _ = PERIODS[self.period]
        return start, end

    def to_dict(self) -> dict:
        out = asdict(self)
        out["start"] = self.start.isoformat() if self.start else None
        out["end"] = self.end.isoformat() if self.end else None
        return out


def _merge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def _number(raw: dict, section: str, key: str, *, low: float, high: float | None = None,
            optional: bool = False, integer: bool = False) -> float | int | None:  # fmt: skip
    value = raw.get(key)
    name = f"{section}.{key}"
    if value is None or value == "":
        if optional:
            return None
        raise SettingsError(f"{name} is required")
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise SettingsError(f"{name} must be a number")
    try:
        number = float(value)
    except ValueError:
        raise SettingsError(f"{name} must be a number, not {value!r}") from None
    if number != number or number < low or (high is not None and number > high):
        span = f"between {low:g} and {high:g}" if high is not None else f"at least {low:g}"
        raise SettingsError(f"{name} must be {span} (got {number:g})")
    if integer:
        if number != int(number):
            raise SettingsError(f"{name} must be a whole number")
        return int(number)
    return number


def _day(value, name: str) -> date:
    try:
        return value if isinstance(value, date) else date.fromisoformat(str(value))
    except ValueError:
        raise SettingsError(f"{name} must be a date like 2015-06-30") from None


def parse(raw: dict | None, defaults: dict | None = None) -> Settings:
    """Settings from the page (``raw``) over the algorithm's ``SETTINGS`` (``defaults``) over
    the Lab's defaults. Raises :class:`SettingsError` with the field's name."""
    if raw is not None and not isinstance(raw, dict):
        raise SettingsError("settings must be an object")
    merged = _merge(_merge(asdict(Settings()), defaults or {}), raw or {})
    unknown = set(merged) - {"period", "start", "end", "universe", "entry", "exit", "book"}
    if unknown:
        raise SettingsError(f"unknown settings: {', '.join(sorted(unknown))}")
    for section in ("universe", "entry", "exit", "book"):
        if not isinstance(merged[section], dict):
            raise SettingsError(f"{section} must be an object")
        known = set(asdict(globals()[section.capitalize()]()))
        extra = set(merged[section]) - known
        if extra:
            raise SettingsError(f"unknown {section} settings: {', '.join(sorted(extra))}")

    period = merged["period"]
    start = end = None
    if period == "custom":
        start = _day(merged.get("start"), "start")
        end = min(_day(merged.get("end"), "end"), LAST_ENTRY)
        if start < date(2005, 1, 1):
            raise SettingsError("start must be on or after 2005-01-01")
        if start > end:
            raise SettingsError("start must come before end (the last entry is 2023-10-13)")
    elif period not in PERIODS:
        raise SettingsError(f"period must be one of {', '.join([*PERIODS, 'custom'])}")

    u, e, x, b = merged["universe"], merged["entry"], merged["exit"], merged["book"]
    universe = Universe(
        min_market_cap=_number(u, "universe", "min_market_cap", low=0),
        max_market_cap=_number(u, "universe", "max_market_cap", low=0, optional=True),
        min_price=_number(u, "universe", "min_price", low=0),
        min_dollar_volume=_number(u, "universe", "min_dollar_volume", low=0),
        exclude_blank_checks=u.get("exclude_blank_checks", False),
    )
    if not isinstance(universe.exclude_blank_checks, bool):
        raise SettingsError("universe.exclude_blank_checks must be true or false")
    if universe.max_market_cap is not None and universe.max_market_cap <= universe.min_market_cap:
        raise SettingsError("universe.max_market_cap must be above universe.min_market_cap")
    if e.get("mode") not in ("signal", "rank"):
        raise SettingsError("entry.mode must be 'signal' or 'rank'")
    if e.get("rank_order", "highest") not in ("highest", "lowest"):
        raise SettingsError("entry.rank_order must be 'highest' or 'lowest'")
    entry = Entry(
        mode=e["mode"],
        top_n=_number(e, "entry", "top_n", low=1, high=500, integer=True),
        rank_order=e.get("rank_order", "highest"),
    )
    exit_ = Exit(
        hold_days=_number(x, "exit", "hold_days", low=1, high=MAX_HOLD, integer=True),
        stop_loss=_number(x, "exit", "stop_loss", low=0.001, high=0.99, optional=True),
        take_profit=_number(x, "exit", "take_profit", low=0.001, high=100, optional=True),
    )
    book = Book(
        position_size=_number(b, "book", "position_size", low=100, high=10_000_000),
        max_positions=_number(b, "book", "max_positions", low=0, high=10_000, integer=True),
    )
    settings = Settings(period, start, end, universe, entry, exit_, book)
    if settings.window()[1] >= HOLDOUT_START:  # cannot happen; the seal is checked anyway
        raise SettingsError("The period reaches into the holdout.")
    return settings
