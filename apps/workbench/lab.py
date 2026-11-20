"""The Lab's endpoints (decision 0023): the owner's algorithms, runs and their results.

Every function takes plain values and returns ``(status, payload)``, so the HTTP handler stays
thin and the endpoints are tested without a server. The owner's code is never imported or run
here: the server writes the run folder and starts a worker process (``kinn.lab.worker``)."""

from __future__ import annotations

import ast
import csv
import io
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path

import duckdb

from apps.workbench import screen_lab
from kinn.lab import data as lab_data
from kinn.lab import store
from kinn.lab.check import as_dicts, check
from kinn.lab.settings import (
    LAST_ENTRY,
    MAX_HOLD,
    PERIODS,
    SWEEPABLE,
    Settings,
    SettingsError,
    parse,
    sweep_settings,
)

Response = tuple[int, object]
_START = threading.Lock()  # one run starts at a time, even with two clicks
SORTABLE = ("entry_date", "exit_date", "signal_date", "ticker", "net", "gross", "net_2x",
            "profit", "over", "sessions", "value", "reason", "side")  # fmt: skip
MAX_PAGE = 500


def literal_settings(code: str) -> dict | None:
    """The algorithm's ``SETTINGS`` when it is a plain literal, read without running the code.
    None when there is none or it is computed."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) and node.value else [])  # fmt: skip
        if any(isinstance(t, ast.Name) and t.id == "SETTINGS" for t in targets):
            try:
                found = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                return None
            return found if isinstance(found, dict) else None
    return None


def _error(status: int, message: str) -> Response:
    return status, {"error": message}


def meta(root: Path) -> Response:
    defaults = Settings().to_dict()
    return 200, {
        "fields": lab_data.catalog(),
        "periods": [{"name": k, "start": str(v[0]), "end": str(v[1]), "label": v[2]}
                    for k, v in PERIODS.items()],  # fmt: skip
        "defaults": defaults, "last_entry": str(LAST_ENTRY), "max_hold": MAX_HOLD,
        "max_code": store.MAX_CODE, "active_run": store.active_run(root),
        "folder": str(root), "sweepable": list(SWEEPABLE),
    }  # fmt: skip


def templates() -> Response:
    return 200, store.templates()


def algorithms(root: Path) -> Response:
    return 200, store.algorithms(root)


def algorithm(root: Path, name: str) -> Response:
    try:
        code = store.read_algorithm(root, name)
    except store.LabError as error:
        return _error(404, str(error))
    return 200, {"name": name, "code": code, "description": store.describe(code),
                 "settings_in_code": literal_settings(code)}  # fmt: skip


def lint(root: Path, body: dict) -> Response:
    """The checks of :mod:`kinn.lab.check` on code the page sends (never run)."""
    code = body.get("code")
    if not isinstance(code, str) or len(code) > store.MAX_CODE:
        return _error(400, "Send the code as text, at most 200,000 characters.")
    library = set(store.library_code(root))
    return 200, {"findings": as_dicts(check(code, library, module=bool(body.get("module"))))}


def format_code(body: dict) -> Response:
    """The code laid out by ruff's formatter (it reads the code; it never runs it)."""
    code = body.get("code")
    if not isinstance(code, str) or len(code) > store.MAX_CODE:
        return _error(400, "Send the code as text, at most 200,000 characters.")
    command = [sys.executable, "-m", "ruff", "format", "--isolated", "--line-length", "100",
               "--stdin-filename", "algorithm.py", "-"]  # fmt: skip
    try:
        done = subprocess.run(command, input=code, capture_output=True, text=True, timeout=15,
                              check=False)  # fmt: skip
    except (OSError, subprocess.TimeoutExpired) as error:
        return _error(501, f"The formatter could not run: {error}")
    if done.returncode != 0:
        if "No module named ruff" in done.stderr:
            return _error(501, "Formatting needs ruff (uv sync installs it).")
        reason = next((line for line in done.stderr.splitlines() if line.strip()), "")
        return _error(400, f"The code could not be formatted: {reason}")
    return 200, {"code": done.stdout}


def from_screen(root: Path, body: dict) -> Response:
    """Make a new algorithm from a Screener screen (its address query) and return its name."""
    query, title = body.get("query"), str(body.get("title") or "screen")[:80]
    if not isinstance(query, str) or len(query) > 4_000:
        return _error(400, "Send the screen as its address query.")
    try:
        code = screen_lab.algorithm(query, title)
        name = screen_lab.name_for(title, {a["name"] for a in store.algorithms(root)})
        store.save_algorithm(root, name, code)
    except (screen_lab.ScreenError, store.LabError) as error:
        return _error(400, str(error))
    return 201, {"name": name}


def library(root: Path) -> Response:
    return 200, store.modules(root)


def module(root: Path, name: str) -> Response:
    try:
        code = store.read_module(root, name)
    except store.LabError as error:
        return _error(404, str(error))
    return 200, {"name": name, "code": code, "description": store.describe(code)}


def save_module(root: Path, name: str, body: dict) -> Response:
    try:
        return 200, store.save_module(root, name, body.get("code"))
    except store.LabError as error:
        return _error(400, str(error))


def delete_module(root: Path, name: str) -> Response:
    try:
        store.delete_module(root, name)
    except store.LabError as error:
        return _error(404, str(error))
    return 200, {"deleted": name}


def versions(root: Path, kind: str, name: str, version: str | None) -> Response:
    """Earlier versions of an algorithm or a helper module, or the code of one of them."""
    try:
        if version is None:
            found = store.history(root, name) if kind == "algorithm" else store.module_history(
                root, name)  # fmt: skip
            return 200, found
        code = store.read_version(root, name, version) if kind == "algorithm" else \
            store.read_module_version(root, name, version)  # fmt: skip
    except store.LabError as error:
        return _error(404, str(error))
    return 200, {"version": version, "code": code}


def save(root: Path, name: str, body: dict) -> Response:
    try:
        return 200, store.save_algorithm(root, name, body.get("code"))
    except store.LabError as error:
        return _error(400, str(error))


def delete(root: Path, name: str) -> Response:
    try:
        store.delete_algorithm(root, name)
    except store.LabError as error:
        return _error(404, str(error))
    return 200, {"deleted": name}


def start(root: Path, body: dict, launch: Callable[[Path], object] = store.launch) -> Response:
    """Save the code, write the run folder and start the worker, or queue the run behind the
    one going. 409 when the queue is full."""
    name, code, settings = body.get("algorithm"), body.get("code"), body.get("settings") or {}
    sweep = body.get("sweep") or None
    if not isinstance(settings, dict):
        return _error(400, "settings must be an object")
    try:
        store.check_name(name)
        if code is None:
            code = store.read_algorithm(root, name)
        # The code and the settings are checked here, so a mistake shows at once and makes no
        # run; the worker checks again with the SETTINGS the code computes, if it computes them.
        errors = [f for f in check(code, set(store.library_code(root))) if f.severity == "error"]
        if errors:
            first = errors[0]
            return _error(400, f"Line {first.line}: {first.message}")
        parse(settings, literal_settings(code) or {})
        sweep_settings(settings, literal_settings(code) or {}, sweep)
        store.save_algorithm(root, name, code)  # Run keeps the code, even if it has to wait
    except (store.LabError, SettingsError) as error:
        return _error(400, str(error))
    with _START:
        digest = store.run_hash(root, code, settings, sweep)
        twin = store.live_twin(root, name, digest)
        if twin:
            return _error(409, f"The same code with the same settings is already in run {twin}.")
        done = None if body.get("again") else store.finished_twin(root, name, digest)
        if done:
            return 409, {
                "error": "This code with these settings has run before, with the same result. "
                         "Running it again adds a trial.",
                "ran_before": done["run_id"],
            }  # fmt: skip
        if len(store.waiting_runs(root)) >= store.MAX_WAITING:
            return _error(409, f"{store.MAX_WAITING} runs are waiting already. Let some finish "
                               "or cancel some first.")  # fmt: skip
        run_dir = store.new_run(root, name, code, settings, sweep, wait=True)
        store.dispatch(root, launch)
    found = store.status(run_dir)
    if found.get("state") == "failed":
        return _error(500, found.get("error") or "The worker process could not start.")
    return 202, {"run_id": run_dir.name, "status": _placed(root, run_dir, found)}


def _placed(root: Path, run_dir: Path, found: dict) -> dict:
    """A waiting run's status says how many runs are ahead of it."""
    if found.get("state") != "waiting":
        return found
    queue = [r.name for r in store.waiting_runs(root)]
    ahead = queue.index(run_dir.name) if run_dir.name in queue else len(queue)
    return {**found, "ahead": ahead + (1 if store.active_run(root) else 0)}


def keep_dispatching(
    root: Path,
    launch: Callable[[Path], object] = store.launch,
    every: float = 2.0,
    stop: threading.Event | None = None,
) -> None:
    """Start the next queued run whenever none is going, for as long as the Workbench runs."""
    stop = stop or threading.Event()
    while not stop.wait(every):
        try:
            with _START:
                store.dispatch(root, launch)
        except OSError:
            continue


def _run(root: Path, run_id: str) -> Path:
    return store.run_dir_of(root, run_id)


def runs(root: Path, algorithm: str | None) -> Response:
    if algorithm:
        try:
            store.check_name(algorithm)
        except store.LabError as error:
            return _error(400, str(error))
    return 200, store.list_runs(root, algorithm)


def run_detail(root: Path, run_id: str) -> Response:
    try:
        run_dir = _run(root, run_id)
    except store.LabError as error:
        return _error(404, str(error))
    return 200, {
        "run_id": run_id,
        "status": _placed(root, run_dir, store.status(run_dir)),
        "manifest": store._read(run_dir / "manifest.json"),
        "summary": store.result(run_dir, "summary"),
        "note": store.note(run_dir).strip(),
    }


def save_note(root: Path, run_id: str, body: dict) -> Response:
    try:
        run_dir = _run(root, run_id)
    except store.LabError as error:
        return _error(404, str(error))
    try:
        return 200, {"run_id": run_id, "note": store.set_note(run_dir, body.get("note")).strip()}
    except store.LabError as error:
        return _error(400, str(error))


def run_part(root: Path, run_id: str, part: str) -> Response:
    try:
        run_dir = _run(root, run_id)
        if part == "status":
            return 200, _placed(root, run_dir, store.status(run_dir))
        if part == "code":
            return 200, {"code": (run_dir / "algorithm.py").read_text()}
        if part == "log":
            log = run_dir / "log.txt"
            text = log.read_text(errors="replace")[-20_000:] if log.exists() else ""
            return 200, {"log": text}
        names = {"stocks": "by_stock", "years": "by_year", "equity": "equity",
                 "lookahead": "lookahead", "summary": "summary", "path": "path",
                 "factor": "factor", "sweep": "sweep", "luck": "luck"}  # fmt: skip
        if part not in names:
            return _error(404, "Unknown part of a run.")
        found = store.result(run_dir, names[part])
    except store.LabError as error:
        return _error(404, str(error))
    return (200, found) if found is not None else _error(404, "This run has no results yet.")


def cancel(root: Path, run_id: str) -> Response:
    try:
        return 200, store.cancel(_run(root, run_id))
    except store.LabError as error:
        return _error(409 if "not running" in str(error) else 404, str(error))


def _parquet(path: Path) -> str:
    return "read_parquet('" + str(path).replace("'", "''") + "')"


def _first(query: dict, key: str, default: str = "") -> str:
    values = query.get(key) or [default]
    return values[0]


def trades(root: Path, run_id: str, query: dict) -> Response:
    """A page of a run's trades: filter by ticker and by the book, sort, page."""
    try:
        path = _run(root, run_id) / "trades.parquet"
    except store.LabError as error:
        return _error(404, str(error))
    if not path.exists():
        return _error(404, "This run has no trades file.")
    sort = _first(query, "sort", "entry_date")
    if sort not in SORTABLE:
        return _error(400, f"sort must be one of {', '.join(SORTABLE)}")
    order = "desc" if _first(query, "order", "asc") == "desc" else "asc"
    try:
        offset = max(int(_first(query, "offset", "0")), 0)
        limit = min(max(int(_first(query, "limit", "100")), 1), MAX_PAGE)
    except ValueError:
        return _error(400, "offset and limit must be whole numbers")
    where, params = ["true"], []
    ticker = _first(query, "ticker").strip().upper()
    if ticker:
        where.append("upper(ticker) = ?")
        params.append(ticker)
    book = _first(query, "book")
    if book in ("taken", "skipped"):
        where.append("taken" if book == "taken" else "not taken")
    con = duckdb.connect()
    try:
        source = _parquet(path)
        sql_where = " and ".join(where)
        total = con.execute(f"select count(*) from {source} where {sql_where}", params).fetchone()
        rows = con.execute(
            f"select * from {source} where {sql_where} order by {sort} {order}, entry_date, ticker "
            "limit ? offset ?", [*params, limit, offset],
        ).fetchdf()  # fmt: skip
    finally:
        con.close()
    for column in ("signal_date", "entry_date", "exit_date"):
        if column in rows:
            rows[column] = rows[column].astype(str).str[:10]
    records = rows.astype(object).where(rows.notna(), None).to_dict("records")
    return 200, {"total": int(total[0]) if total else 0, "offset": offset, "limit": limit,
                 "rows": records}  # fmt: skip


def trades_csv(root: Path, run_id: str) -> tuple[int, str]:
    try:
        path = _run(root, run_id) / "trades.parquet"
    except store.LabError as error:
        return 404, str(error)
    if not path.exists():
        return 404, "This run has no trades file."
    con = duckdb.connect()
    try:
        frame = con.execute(f"select * from {_parquet(path)} order by entry_date, ticker").fetchdf()
    finally:
        con.close()
    out = io.StringIO()
    frame.to_csv(out, index=False, quoting=csv.QUOTE_MINIMAL, date_format="%Y-%m-%d")
    return 200, out.getvalue()


# -- routing ------------------------------------------------------------------------------
def route(method: str, parts: list[str], query: dict, body: dict | None, root: Path,
          launch: Callable[[Path], object] = store.launch) -> Response:  # fmt: skip
    """``parts`` is the path after /api/lab/, split on '/'."""
    head = parts[0] if parts else ""
    if method == "GET":
        if parts == ["meta"]:
            return meta(root)
        if parts == ["templates"]:
            return templates()
        if parts == ["algorithms"]:
            return algorithms(root)
        if parts == ["library"]:
            return library(root)
        if head == "library" and len(parts) == 2:
            return module(root, parts[1])
        if head == "algorithms" and len(parts) == 2:
            return algorithm(root, parts[1])
        if head in ("algorithms", "library") and len(parts) in (3, 4) and parts[2] == "history":
            kind = "algorithm" if head == "algorithms" else "module"
            return versions(root, kind, parts[1], parts[3] if len(parts) == 4 else None)
        if parts == ["runs"]:
            return runs(root, _first(query, "algorithm") or None)
        if head == "runs" and len(parts) == 2:
            return run_detail(root, parts[1])
        if head == "runs" and len(parts) == 3 and parts[2] == "trades":
            return trades(root, parts[1], query)
        if head == "runs" and len(parts) == 3:
            return run_part(root, parts[1], parts[2])
    elif method == "PUT" and head == "algorithms" and len(parts) == 2:
        return save(root, parts[1], body or {})
    elif method == "PUT" and head == "library" and len(parts) == 2:
        return save_module(root, parts[1], body or {})
    elif method == "DELETE" and head == "library" and len(parts) == 2:
        return delete_module(root, parts[1])
    elif method == "POST" and parts == ["check"]:
        return lint(root, body or {})
    elif method == "POST" and parts == ["from-screen"]:
        return from_screen(root, body or {})
    elif method == "POST" and parts == ["format"]:
        return format_code(body or {})
    elif method == "DELETE" and head == "algorithms" and len(parts) == 2:
        return delete(root, parts[1])
    elif method == "POST" and parts == ["runs"]:
        return start(root, body or {}, launch)
    elif method == "POST" and head == "runs" and len(parts) == 3 and parts[2] == "cancel":
        return cancel(root, parts[1])
    elif method == "PUT" and head == "runs" and len(parts) == 3 and parts[2] == "note":
        return save_note(root, parts[1], body or {})
    return _error(404, "No such Lab endpoint.")
