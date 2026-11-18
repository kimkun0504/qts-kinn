"""The Lab from the terminal (decision 0023): ``kinn lab list``, ``kinn lab run`` and
``kinn lab selfcheck``. A run here goes through the same runner and the same Lab folder as the
Run button, so it shows on the page and counts as a trial the same way."""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from kinn.lab import store
from kinn.lab.check import check
from kinn.lab.runner import run as run_one
from kinn.lab.settings import SettingsError, parse

SELFCHECK_PERIOD = {"period": "custom", "start": "2015-01-02", "end": "2015-12-31"}
PEEK = '''"""A deliberate peek at the next day, to show the lookahead test works."""

def signal(data):
    return data.returns.shift(-1) > 0
'''


def _pct(value: float | None, digits: int = 2) -> str:
    return "-" if value is None else f"{100 * value:+.{digits}f}%"


def _money(value: float | None) -> str:
    return "-" if value is None else f"{'-' if value < 0 else '+'}${abs(value):,.0f}"


def list_algorithms(root: Path) -> int:
    rows = store.algorithms(root)
    if not rows:
        print(f"No algorithms yet in {root}.")
        return 0
    width = max(len(r["name"]) for r in rows)
    for r in sorted(rows, key=lambda r: r["name"]):
        last = r["last_run"] or {}
        result = last.get("headline") or last.get("state") or "no runs"
        print(f"{r['name']:<{width}}  {r['trials']:>3} trials  {result}")
    return 0


def _resolve(root: Path, target: str) -> tuple[str, str]:
    """(name, code) for an algorithm in the Lab folder or a .py file anywhere."""
    path = Path(target).expanduser()
    if path.suffix == ".py" and path.exists():
        name = re.sub(r"[^a-z0-9_-]+", "_", path.stem.lower()).strip("-_")[:64] or "algorithm"
        return name, path.read_text()
    return target, store.read_algorithm(root, target)


def run_algorithm(root: Path, target: str, settings: dict, *, time_limit: float | None,
                  out: Callable[[str], None] = print,
                  runner: Callable[..., None] = run_one) -> int:  # fmt: skip
    """Run one algorithm and print what it made. 0 when the run completes."""
    try:
        name, code = _resolve(root, target)
        store.check_name(name)
        parse(settings, {})  # the settings alone; the code's SETTINGS are applied in the run
    except (store.LabError, SettingsError) as error:
        out(f"refused: {error}")
        return 2
    errors = [f for f in check(code, set(store.library_code(root))) if f.severity == "error"]
    if errors:
        for f in errors:
            out(f"{name}.py, line {f.line}: {f.message}")
        return 2
    active = store.active_run(root)
    if active:
        out(f"refused: run {active} is still going (one run at a time)")
        return 2
    store.save_algorithm(root, name, code)
    run_dir = store.new_run(root, name, code, settings)
    (run_dir / "pid").write_text(str(os.getpid()))
    out(f"run {run_dir.name}")
    started = time.time()
    runner(run_dir, time_limit=time_limit)
    state = store.status(run_dir)
    if state["state"] != "complete":
        out(f"{state['state']}: {state.get('error', '')}")
        return 1
    summary = store.result(run_dir, "summary") or {}
    stocks = store.result(run_dir, "by_stock") or []
    look = summary.get("lookahead", {})
    out(f"{summary.get('headline')}  ({time.time() - started:.1f} s, trial "
        f"{summary.get('trial_number')}, {summary.get('period_label')})")  # fmt: skip
    out(f"  won {100 * (summary.get('win_rate') or 0):.0f}%, at 2x costs "
        f"{_pct(summary.get('mean_net_2x'))}, weekly t {summary.get('t_weekly') or 0:.2f}, "
        f"book {_money(summary.get('book_profit'))}, worst drawdown "
        f"{_money(summary.get('max_drawdown'))}")  # fmt: skip
    if not look.get("passed", True):
        out(f"  THE CODE LOOKS AHEAD: {look.get('detail')}")
    if stocks:
        best = ", ".join(f"{s['ticker']} {_money(s['profit'])}" for s in stocks[:5])
        worst = ", ".join(f"{s['ticker']} {_money(s['profit'])}" for s in stocks[-5:][::-1])
        out(f"  best:  {best}")
        out(f"  worst: {worst}")
    out(f"  results in {run_dir}")
    return 0


def selfcheck(out: Callable[[str], None] = print, runner: Callable[..., None] = run_one,
              period: dict | None = None) -> int:  # fmt: skip
    """Run every template, and a deliberate peek, on one year in a scratch Lab folder (the
    owner's algorithms and trial counts are untouched). 0 when everything behaves."""
    period = period or SELFCHECK_PERIOD
    failures = 0
    with tempfile.TemporaryDirectory(prefix="kinn-lab-check-") as tmp:
        root = Path(tmp)
        for template in store.templates():
            found = [f for f in check(template["code"]) if f.severity == "error"]
            if found:
                out(f"FAIL {template['name']}: the code check found {found[0].message}")
                failures += 1
                continue
            name = template["name"].replace("_", "-")
            run_dir = store.new_run(root, name, template["code"], period)
            started = time.time()
            runner(run_dir, time_limit=600)
            state = store.status(run_dir)
            summary = store.result(run_dir, "summary") or {}
            ok = state["state"] == "complete" and summary.get("lookahead", {}).get("passed")
            failures += not ok
            what = summary.get("headline") if ok else state.get("error") or "lookahead failed"
            out(f"{'ok  ' if ok else 'FAIL'} {template['name']:<16} {time.time() - started:5.1f} s"
                f"  {what}")  # fmt: skip
        run_dir = store.new_run(root, "peek", PEEK, period)
        runner(run_dir, time_limit=600)
        caught = not (store.result(run_dir, "lookahead") or {}).get("passed", True)
        failures += not caught
        out(f"{'ok  ' if caught else 'FAIL'} the lookahead test "
            f"{'caught' if caught else 'MISSED'} a deliberate peek")  # fmt: skip
    out("self-check passed" if not failures else f"self-check: {failures} problem(s)")
    return 1 if failures else 0


def settings_from(args) -> dict:
    """The settings the command line asks for, as the page would send them."""
    settings: dict = json.loads(args.settings) if args.settings else {}
    if args.period:
        settings["period"] = args.period
    if args.start or args.end:
        settings.update(period="custom", start=args.start, end=args.end)
    return settings
