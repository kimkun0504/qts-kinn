"""Load the owner's algorithm, call it, and test it for lookahead.

The code runs in the worker process (never in the Workbench server). Errors are reported with
the line in the owner's file, not the Lab's internals.
"""

from __future__ import annotations

import traceback
import types
from dataclasses import dataclass

import numpy as np
import pandas as pd

from kinn.lab.data import LabData

FILE = "algorithm.py"


class AlgorithmError(Exception):
    """The algorithm could not be loaded or returned something the Lab cannot use. The message
    is written for the owner, with the line of his code where it went wrong."""


@dataclass
class Algorithm:
    module: types.ModuleType
    description: str

    @property
    def settings(self) -> dict:
        found = getattr(self.module, "SETTINGS", None)
        if found is None:
            return {}
        if not isinstance(found, dict):
            raise AlgorithmError(
                "SETTINGS must be a dict, for example {'exit': {'hold_days': 20}}."
            )
        return found

    @property
    def has_exit(self) -> bool:
        return callable(getattr(self.module, "exit_signal", None))


def _user_trace(error: BaseException) -> str:
    """The traceback from the owner's file down, with his line numbers."""
    frames = traceback.extract_tb(error.__traceback__)
    mine = [i for i, frame in enumerate(frames) if frame.filename == FILE]
    frames = frames[mine[0] :] if mine else frames[-1:]
    lines = []
    for frame in frames:
        if frame.filename == FILE:
            where = "your code"
        elif "/pkg/lab/" in frame.filename.replace("\\", "/"):
            where = "lab/" + frame.filename.replace("\\", "/").rsplit("/", 1)[-1]  # the library
        else:
            where = frame.filename.rsplit("/", 2)[-1]
        lines.append(f"  {where}, line {frame.lineno}, in {frame.name}")
        if frame.line:
            lines.append(f"    {frame.line}")
    lines.append(f"{type(error).__name__}: {error}")
    return "\n".join(lines)


def load(code: str) -> Algorithm:
    module = types.ModuleType("algorithm")
    module.__file__ = FILE
    try:
        compiled = compile(code, FILE, "exec")
    except SyntaxError as error:
        where = f"line {error.lineno}" + (f", column {error.offset}" if error.offset else "")
        text = (error.text or "").rstrip()
        raise AlgorithmError(f"Syntax error at {where}: {error.msg}\n    {text}") from None
    try:
        exec(compiled, module.__dict__)  # noqa: S102 - the owner's own code, in the worker
    except Exception as error:  # noqa: BLE001 - any failure while loading is reported
        raise AlgorithmError("Your code failed while loading:\n" + _user_trace(error)) from None
    if not callable(getattr(module, "signal", None)):
        raise AlgorithmError("Your code needs a function `signal(data)` that returns a table of "
                             "True/False (or scores) by date and stock.")  # fmt: skip
    return Algorithm(module, (module.__doc__ or "").strip().split("\n")[0])


def _call(algorithm: Algorithm, name: str, data: LabData) -> pd.DataFrame:
    try:
        out = getattr(algorithm.module, name)(data)
    except AttributeError as error:
        if "data has no field" in str(error):  # the message says it all; then where it was
            where = "\n".join(_user_trace(error).splitlines()[:-1])
            raise AlgorithmError(f"{name}(data): {error}\n{where}") from None
        raise AlgorithmError(f"{name}(data) failed:\n" + _user_trace(error)) from None
    except MemoryError:
        raise AlgorithmError(f"{name}(data) ran out of memory. Use fewer fields, a shorter "
                             "period or a narrower universe.") from None  # fmt: skip
    except Exception as error:  # noqa: BLE001
        raise AlgorithmError(f"{name}(data) failed:\n" + _user_trace(error)) from None
    return _shape(out, data, name)


def _shape(out, data: LabData, name: str) -> pd.DataFrame:
    """Accept a DataFrame aligned with the data (or a same-shaped array); return it aligned."""
    dates, stocks = data.dates, data.stocks
    if isinstance(out, pd.DataFrame):
        if not out.index.equals(dates):
            missing = dates.difference(out.index)
            if len(out.index.difference(dates)):
                raise AlgorithmError(f"{name}(data) returned dates that are not in the data.")
            if len(missing) > len(dates) // 2:
                raise AlgorithmError(f"{name}(data) returned a table that is missing most dates; "
                                     "return a table with data's dates as its rows.")  # fmt: skip
            fill = False if all(pd.api.types.is_bool_dtype(t) for t in out.dtypes) else np.nan
            out = out.reindex(dates, fill_value=fill)
        if not out.columns.equals(stocks):
            extra = out.columns.difference(stocks)
            if len(extra):
                raise AlgorithmError(f"{name}(data) returned stocks that are not in the data: "
                                     f"{', '.join(map(str, extra[:5]))}")  # fmt: skip
            fill = False if all(pd.api.types.is_bool_dtype(t) for t in out.dtypes) else np.nan
            out = out.reindex(columns=stocks, fill_value=fill)
        return out
    if isinstance(out, np.ndarray) and out.shape == (len(dates), len(stocks)):
        return pd.DataFrame(out, index=dates, columns=stocks)
    if isinstance(out, pd.Series):
        raise AlgorithmError(f"{name}(data) returned one column (a Series). It must return a table "
                             "with a column for every stock, like data.close does.")  # fmt: skip
    raise AlgorithmError(f"{name}(data) must return a pandas DataFrame shaped like data.close "
                         f"(dates × stocks), not {type(out).__name__}.")  # fmt: skip


def to_entries(frame: pd.DataFrame, mode: str, name: str = "signal") -> np.ndarray:
    """Signal mode: a boolean array. Rank mode: a float array of scores (NaN = no score)."""
    usable = (pd.api.types.is_bool_dtype(t) or pd.api.types.is_numeric_dtype(t)
              for t in frame.dtypes)  # fmt: skip
    if not all(usable):
        what = "numbers (scores)" if mode == "rank" else "True/False"
        raise AlgorithmError(f"{name}(data) must return {what}, not text or objects. Check the "
                             "table's dtypes.")  # fmt: skip
    values = frame.to_numpy()
    if mode == "rank":
        try:
            scores = values.astype(np.float64)
        except (TypeError, ValueError):
            raise AlgorithmError(
                f"In rank mode {name}(data) must return numbers (scores)."
            ) from None
        scores[~np.isfinite(scores)] = np.nan
        return scores
    if values.dtype == bool:
        return values
    try:
        numbers = values.astype(np.float64)
    except (TypeError, ValueError):
        raise AlgorithmError(
            f"{name}(data) must return True/False (or numbers in rank mode)."
        ) from None
    return np.isfinite(numbers) & (numbers != 0)


def signals(algorithm: Algorithm, data: LabData, mode: str) -> tuple[np.ndarray, np.ndarray | None]:
    entries = to_entries(_call(algorithm, "signal", data), mode)
    exits = None
    if algorithm.has_exit:
        exits = to_entries(_call(algorithm, "exit_signal", data), "signal", "exit_signal")
    return entries, exits


def lookahead(algorithm: Algorithm, data: LabData, mode: str,
              entries: np.ndarray, exits: np.ndarray | None) -> dict:  # fmt: skip
    """Run the algorithm again on the data cut off at two sessions inside the period. A signal
    on a row may only depend on that row and earlier ones, so the rows up to each cut-off must
    come out the same. Returns what was found, with the first difference if any."""
    first, last = data.first_row, data.last_signal_row
    span = last - first
    checked = []
    for share in (0.4, 0.75):
        cut = first + int(span * share)
        if cut <= first + 5:
            continue
        rows = cut + 1
        view = data.cut(rows)
        try:
            again, again_exit = signals(algorithm, view, mode)
        except AlgorithmError as error:
            day = data.dates[cut].date()
            return {"passed": False, "checked": checked,
                    "detail": f"Your code failed on data cut off at {day}: {error}"}  # fmt: skip
        for label, full, part in (("signal", entries, again), ("exit_signal", exits, again_exit)):
            if full is None or part is None:
                continue
            a, b = full[:rows], part[:rows]
            if mode == "rank" and label == "signal":
                same = np.isclose(a, b, rtol=1e-5, atol=1e-9, equal_nan=True)
            else:
                same = a == b
            if not same.all():
                r, c = np.argwhere(~same)[0]
                return {
                    "passed": False, "checked": checked + [str(data.dates[cut].date())],
                    "detail": (f"{label}(data) changed when the data was cut off at "
                               f"{data.dates[cut].date()}: on {data.dates[r].date()} for "
                               f"{data.stocks[c]} it gave {a[r, c]} with the later data and "
                               f"{b[r, c]} without it. The code uses data from after the day it "
                               "signals (look for shift(-1), centered windows, or whole-column "
                               "statistics such as .mean() over all dates)."),
                }  # fmt: skip
        checked.append(str(data.dates[cut].date()))
    return {"passed": True, "checked": checked, "detail": ""}
