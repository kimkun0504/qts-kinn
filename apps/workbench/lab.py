"""The Lab's endpoints (decision 0023): the owner's algorithms, runs and their results.

Every function takes plain values and returns ``(status, payload)``, so the HTTP handler stays
thin and the endpoints are tested without a server. The owner's code is never imported or run
here: the server writes the run folder and starts a worker process (``kinn.lab.worker``)."""

from __future__ import annotations

import ast
import csv
import io
import threading
from collections.abc import Callable
from pathlib import Path

import duckdb

from kinn.lab import data as lab_data
from kinn.lab import store
from kinn.lab.settings import LAST_ENTRY, MAX_HOLD, PERIODS, Settings, SettingsError, parse

Response = tuple[int, object]
_START = threading.Lock()  # one run starts at a time, even with two clicks
SORTABLE = ("entry_date", "exit_date", "signal_date", "ticker", "net", "gross", "net_2x",
            "profit", "over", "sessions", "value", "reason")  # fmt: skip
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
        "folder": str(root),
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
    """Save the code, write the run folder and start the worker. 409 while another runs."""
    name, code, settings = body.get("algorithm"), body.get("code"), body.get("settings") or {}
    if not isinstance(settings, dict):
        return _error(400, "settings must be an object")
    try:
        store.check_name(name)
        if code is None:
            code = store.read_algorithm(root, name)
        # Settings are checked here too, so a typo shows at once; the worker checks again with
        # the SETTINGS the code computes, if it computes them.
        parse(settings, literal_settings(code) or {})
    except (store.LabError, SettingsError) as error:
        return _error(400, str(error))
    with _START:
        active = store.active_run(root)
        if active:
            return _error(409, f"Run {active} is still going. Wait for it or cancel it.")
        store.save_algorithm(root, name, code)
        run_dir = store.new_run(root, name, code, settings)
        launch(run_dir)
    return 202, {"run_id": run_dir.name, "status": store.status(run_dir)}


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
        "status": store.status(run_dir),
        "manifest": store._read(run_dir / "manifest.json"),
        "summary": store.result(run_dir, "summary"),
    }


def run_part(root: Path, run_id: str, part: str) -> Response:
    try:
        run_dir = _run(root, run_id)
        if part == "status":
            return 200, store.status(run_dir)
        if part == "code":
            return 200, {"code": (run_dir / "algorithm.py").read_text()}
        if part == "log":
            log = run_dir / "log.txt"
            text = log.read_text(errors="replace")[-20_000:] if log.exists() else ""
            return 200, {"log": text}
        names = {"stocks": "by_stock", "years": "by_year", "equity": "equity",
                 "lookahead": "lookahead", "summary": "summary"}  # fmt: skip
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
        if head == "algorithms" and len(parts) == 2:
            return algorithm(root, parts[1])
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
    elif method == "DELETE" and head == "algorithms" and len(parts) == 2:
        return delete(root, parts[1])
    elif method == "POST" and parts == ["runs"]:
        return start(root, body or {}, launch)
    elif method == "POST" and head == "runs" and len(parts) == 3 and parts[2] == "cancel":
        return cancel(root, parts[1])
    return _error(404, "No such Lab endpoint.")
