"""The Lab folder: the owner's algorithms and the Lab's runs (decision 0023).

<KINN_LAB_DIR or beside the run store>/lab/
    algorithms/<name>.py        the owner's algorithms
    library/<name>.py           helper modules an algorithm imports as ``lab.<name>``
    history/<name>/<time>.py    every earlier version of an algorithm, kept at each save
    history/library-<name>/     the same for a helper module
    trash/                      deleted files (kept, never removed by the Lab)
    cache/                      prices kept between runs (rebuilt when missing)
    runs/<run_id>/              algorithm.py, pkg/lab/ (the library as it was), request.json,
                                manifest.json, status.json, pid, log.txt, results
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import keyword
import os
import re
import signal as signals
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from kinn.core.settings import Settings, load_settings

NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
MODULE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")  # importable: lab.<name>
RESERVED = {"library"}  # a path segment of the page
MAX_CODE = 200_000  # characters
KEEP_VERSIONS = 200  # earlier versions kept a file; the oldest go first
VERSION = re.compile(r"^\d{8}T\d{12}Z$")
TEMPLATES = Path(__file__).parent / "templates"
STATES = ("waiting", "queued", "running", "complete", "failed", "cancelled", "interrupted")
LIVE = ("waiting", "queued", "running")
MAX_WAITING = 20
FINAL = ("complete", "failed", "cancelled", "interrupted")
START_GRACE = 120  # seconds a queued run may wait for its worker before it counts as lost
NOTE_MAX = 2_000


class LabError(ValueError):
    """A request the Lab refuses, with a message for the page."""


def lab_dir(settings: Settings | None = None) -> Path:
    settings = settings or load_settings()
    return Path(os.environ.get("KINN_LAB_DIR") or settings.runs_dir.parent / "lab")


def _write(path: Path, payload: dict) -> None:
    """Write JSON so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=1, default=str) + "\n")
    os.replace(tmp, path)


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def check_name(name: str) -> str:
    if not isinstance(name, str) or not NAME.match(name):
        raise LabError("A name is 1 to 64 characters: lower-case letters, digits, - and _, "
                       "starting with a letter or digit.")  # fmt: skip
    if name in RESERVED:
        raise LabError(f"{name} is a word the Lab keeps for itself. Choose another name.")
    return name


def check_module(name: str) -> str:
    if not isinstance(name, str) or not MODULE.match(name) or keyword.iskeyword(name):
        raise LabError("A helper module's name is 1 to 64 characters: lower-case letters, digits "
                       "and _, starting with a letter, so it can be imported.")  # fmt: skip
    return name


def describe(code: str) -> str:
    """The first line of the module docstring, or ''."""
    match = re.match(r'\s*(?:#.*\n\s*)*[rRuU]?("""|\'\'\')(.*?)(\1)', code, re.S)
    if not match:
        return ""
    lines = [line.strip() for line in match.group(2).strip().splitlines()]
    return lines[0] if lines else ""


# -- algorithms ---------------------------------------------------------------------------
def algorithms(root: Path) -> list[dict]:
    folder = root / "algorithms"
    runs = list_runs(root)
    out = []
    for path in sorted(folder.glob("*.py")) if folder.exists() else []:
        code = path.read_text()
        mine = [r for r in runs if r.get("algorithm") == path.stem]
        out.append({
            "name": path.stem, "description": describe(code),
            "updated": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            "runs": len(mine), "trials": sum(r.get("trials", 0) for r in mine),
            "last_run": mine[0] if mine else None,
        })  # fmt: skip
    return out


def read_algorithm(root: Path, name: str) -> str:
    path = root / "algorithms" / f"{check_name(name)}.py"
    if not path.exists():
        raise LabError(f"There is no algorithm called {name}.")
    return path.read_text()


def _replace(path: Path, code: str, history: Path) -> None:
    """Write ``code`` to ``path`` so a reader never sees half a file, first keeping what was
    there in ``history`` when it differs: no save can lose earlier work."""
    if not isinstance(code, str):
        raise LabError("The code must be text.")
    if len(code) > MAX_CODE:
        raise LabError(f"The code is longer than {MAX_CODE:,} characters.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        before = path.read_text()
        if before != code:
            history.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            (history / f"{stamp}.py").write_text(before)
            for old in sorted(history.glob("*.py"))[:-KEEP_VERSIONS]:
                old.unlink(missing_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(code)
    os.replace(tmp, path)


def save_algorithm(root: Path, name: str, code: str) -> dict:
    check_name(name)
    _replace(root / "algorithms" / f"{name}.py", code, root / "history" / name)
    return {"name": name, "description": describe(code)}


def _versions(folder: Path) -> list[dict]:
    out = []
    for path in sorted(folder.glob("*.py"), reverse=True) if folder.exists() else []:
        if not VERSION.match(path.stem):
            continue
        code = path.read_text()
        stamp = path.stem
        saved = datetime.strptime(stamp, "%Y%m%dT%H%M%S%fZ").replace(tzinfo=UTC)
        first = (code.splitlines() or [""])[0][:120]
        out.append({"version": stamp, "saved_at": saved.isoformat(),
                    "lines": code.count("\n") + 1, "characters": len(code),
                    "first_line": first})  # fmt: skip
    return out


def _version(folder: Path, version: str) -> str:
    if not isinstance(version, str) or not VERSION.match(version):
        raise LabError("Not a saved version.")
    path = folder / f"{version}.py"
    if not path.exists():
        raise LabError("There is no such saved version.")
    return path.read_text()


def history(root: Path, name: str) -> list[dict]:
    """Earlier versions of an algorithm, newest first: each is what the file held before a
    save changed it."""
    return _versions(root / "history" / check_name(name))


def read_version(root: Path, name: str, version: str) -> str:
    return _version(root / "history" / check_name(name), version)


def delete_algorithm(root: Path, name: str) -> None:
    """Move to trash/, never remove: the runs keep their own copy of the code anyway."""
    path = root / "algorithms" / f"{check_name(name)}.py"
    if not path.exists():
        raise LabError(f"There is no algorithm called {name}.")
    trash = root / "trash"
    trash.mkdir(parents=True, exist_ok=True)
    os.replace(path, trash / f"{name}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.py")


# -- the library: helper modules -----------------------------------------------------------
def modules(root: Path) -> list[dict]:
    folder = root / "library"
    return [
        {"name": path.stem, "description": describe(path.read_text()),
         "updated": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()}
        for path in sorted(folder.glob("*.py")) if MODULE.match(path.stem)
    ]  # fmt: skip


def read_module(root: Path, name: str) -> str:
    path = root / "library" / f"{check_module(name)}.py"
    if not path.exists():
        raise LabError(f"There is no helper module called {name}.")
    return path.read_text()


def save_module(root: Path, name: str, code: str) -> dict:
    check_module(name)
    _replace(root / "library" / f"{name}.py", code, root / "history" / f"library-{name}")
    return {"name": name, "description": describe(code)}


def module_history(root: Path, name: str) -> list[dict]:
    return _versions(root / "history" / f"library-{check_module(name)}")


def read_module_version(root: Path, name: str, version: str) -> str:
    return _version(root / "history" / f"library-{check_module(name)}", version)


def delete_module(root: Path, name: str) -> None:
    path = root / "library" / f"{check_module(name)}.py"
    if not path.exists():
        raise LabError(f"There is no helper module called {name}.")
    trash = root / "trash"
    trash.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    os.replace(path, trash / f"library-{name}-{stamp}.py")


def library_code(root: Path) -> dict[str, str]:
    """Every helper module's code by name, as a run will snapshot it."""
    folder = root / "library"
    return {path.stem: path.read_text() for path in sorted(folder.glob("*.py"))
            if MODULE.match(path.stem)}  # fmt: skip


def templates() -> list[dict]:
    return [
        {"name": path.stem, "description": describe(path.read_text()), "code": path.read_text()}
        for path in sorted(TEMPLATES.glob("*.py"))
    ]


# -- runs ---------------------------------------------------------------------------------
def code_hash(code: str, settings: dict, library: dict[str, str] | None = None) -> str:
    """One hash for everything a run's result depends on that the owner wrote."""
    payload = {"code": code, "settings": settings}
    if library:
        payload["library"] = library
    text = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(text.encode()).hexdigest()


def run_hash(root: Path, code: str, settings: dict, sweep: dict | None = None) -> str:
    """What makes two runs the same: the code, the settings asked for, and the library."""
    return code_hash(code, {**settings, "sweep": sweep} if sweep else settings, library_code(root))


def live_twin(root: Path, name: str, digest: str) -> str | None:
    """A run of the same code and settings that is still going or waiting."""
    for run in list_runs(root, name):
        if run["state"] in LIVE:
            manifest = _read(run_dir_of(root, run["run_id"]) / "manifest.json") or {}
            if manifest.get("code_sha256") == digest:
                return run["run_id"]
    return None


def new_run(
    root: Path,
    name: str,
    code: str,
    settings: dict,
    sweep: dict | None = None,
    *,
    wait: bool = False,
) -> Path:
    """Create the run's folder with its request and a copy of the library as it is now; the
    worker does the rest. A run made to wait stays in the queue until ``dispatch`` starts it."""
    check_name(name)
    digest = run_hash(root, code, settings, sweep)
    library = library_code(root)
    (root / "runs").mkdir(parents=True, exist_ok=True)
    while True:  # two runs of the same code in the same second: the second waits a second
        now = datetime.now(UTC)
        run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}_{name}_{digest[:8]}"
        run_dir = root / "runs" / run_id
        try:
            run_dir.mkdir()
            break
        except FileExistsError:
            time.sleep(0.2)
    (run_dir / "algorithm.py").write_text(code)
    package = run_dir / "pkg" / "lab"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""The owner\'s helper modules, as they were."""\n')
    for module, text in library.items():
        (package / f"{module}.py").write_text(text)
    _write(run_dir / "request.json", {"algorithm": name, "settings": settings, "sweep": sweep})
    _write(run_dir / "manifest.json", {
        "schema": "lab-run-1", "run_id": run_id, "algorithm": name,
        "description": describe(code), "code_sha256": digest,
        "library": {m: hashlib.sha256(t.encode()).hexdigest()[:12] for m, t in library.items()},
        "requested_settings": settings, "requested_sweep": sweep, "created_at": now.isoformat(),
    })  # fmt: skip
    if wait:
        set_status(run_dir, "waiting", stage="In the queue", progress=0.0)
    else:
        set_status(run_dir, "queued", stage="Waiting to start", progress=0.0)
    return run_dir


def set_status(run_dir: Path, state: str, **fields) -> dict:
    """Record the run's state. A finished run stays finished: a late progress note from a
    worker being stopped cannot turn a cancelled run back into a running one."""
    if state not in STATES:
        raise ValueError(f"unknown run state {state!r}")
    status = _read(run_dir / "status.json") or {}
    if status.get("state") in FINAL and state in LIVE:
        return status
    status.update(fields, state=state, updated_at=datetime.now(UTC).isoformat())
    _write(run_dir / "status.json", status)
    return status


def _age(run_dir: Path) -> float:
    """Seconds since the run's state last changed."""
    try:
        return time.time() - (run_dir / "status.json").stat().st_mtime
    except OSError:
        return 0.0


def pid_of(run_dir: Path) -> int | None:
    """The worker's process id. Kept in its own file, written only by the launcher, so the
    launcher and the worker never write the same file."""
    try:
        return int((run_dir / "pid").read_text())
    except (OSError, ValueError):
        return None


def status(run_dir: Path) -> dict:
    found = _read(run_dir / "status.json") or {"state": "failed", "error": "No status file."}
    pid = pid_of(run_dir)
    if found.get("state") == "queued" and not pid and _age(run_dir) > START_GRACE:
        return set_status(run_dir, "interrupted", stage="Stopped",
                          error="The run's worker never started. Run it again.")  # fmt: skip
    if found.get("state") in ("queued", "running") and pid and not alive(pid):
        found = set_status(
            run_dir, "interrupted", stage="Stopped",
            error="The run's process ended without finishing: the Workbench was restarted, "
                  "or the machine ran out of memory. Try a shorter period or a narrower universe.",
        )  # fmt: skip
    return found


def alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # A finished child of this process stays a zombie until waited for; reap it if so.
    try:
        done, _ = os.waitpid(int(pid), os.WNOHANG)
        return done == 0
    except ChildProcessError:
        return True


def run_dir_of(root: Path, run_id: str) -> Path:
    if not re.match(r"^\d{8}T\d{6}Z_[a-z0-9][a-z0-9_-]{0,63}_[0-9a-f]{8}$", run_id or ""):
        raise LabError("Not a Lab run id.")
    path = root / "runs" / run_id
    if not path.exists():
        raise LabError(f"There is no run {run_id}.")
    return path


def note(run_dir: Path) -> str:
    try:
        return (run_dir / "note.txt").read_text()
    except OSError:
        return ""


def set_note(run_dir: Path, text: object) -> str:
    if not isinstance(text, str):
        raise LabError("A note is text.")
    clean = text.strip()
    if len(clean) > NOTE_MAX:
        raise LabError(f"Keep a note under {NOTE_MAX:,} characters.")
    path = run_dir / "note.txt"
    if not clean:
        path.unlink(missing_ok=True)
        return ""
    tmp = path.with_suffix(".txt.tmp")
    tmp.write_text(clean + "\n")
    os.replace(tmp, path)
    return clean + "\n"


def list_runs(root: Path, algorithm: str | None = None) -> list[dict]:
    folder = root / "runs"
    out = []
    for run_dir in folder.iterdir() if folder.exists() else []:
        manifest = _read(run_dir / "manifest.json")
        if not manifest or (algorithm and manifest.get("algorithm") != algorithm):
            continue
        state = status(run_dir)
        summary = _read(run_dir / "summary.json") or {}
        out.append({
            "run_id": manifest["run_id"], "algorithm": manifest["algorithm"],
            "description": manifest.get("description", ""), "created_at": manifest["created_at"],
            "state": state.get("state"), "stage": state.get("stage"), "error": state.get("error"),
            "trial": bool(state.get("signals_computed")),
            "trials": int(state.get("trials") or (1 if state.get("signals_computed") else 0)),
            "period": summary.get("period_label"),
            "headline": summary.get("headline"),
            "trades": summary.get("trades"), "mean_net": summary.get("mean_net"),
            "t_weekly": summary.get("t_weekly"), "sharpe": summary.get("sharpe"),
            "book_profit": summary.get("book_profit"),
            "note": note(run_dir).strip(),
        })  # fmt: skip
    out.sort(key=lambda r: (r["created_at"], r["run_id"]), reverse=True)  # newest first
    return out


def active_run(root: Path) -> str | None:
    for run in list_runs(root):
        if run["state"] in ("queued", "running"):
            return run["run_id"]
    return None


def _created(run_dir: Path) -> str:
    return (_read(run_dir / "manifest.json") or {}).get("created_at", "")


def waiting_runs(root: Path) -> list[Path]:
    """The runs in the queue, the first to start first."""
    folder = root / "runs"
    found = [run_dir for run_dir in (folder.iterdir() if folder.exists() else [])
             if (_read(run_dir / "status.json") or {}).get("state") == "waiting"]  # fmt: skip
    return sorted(found, key=lambda run_dir: (_created(run_dir), run_dir.name))


def dispatch(root: Path, launch) -> Path | None:
    """Start the first run in the queue when no run is going. A run is claimed with a file
    made only if it is not there, so two Workbenches never start the same run."""
    if active_run(root):
        return None
    for run_dir in waiting_runs(root):
        try:
            os.close(os.open(run_dir / "claimed", os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        except FileExistsError:
            continue
        set_status(run_dir, "queued", stage="Waiting to start")
        try:
            launch(run_dir)
        except OSError as error:
            set_status(run_dir, "failed", stage="Stopped",
                       error=f"The worker process could not start: {error}")  # fmt: skip
            continue
        return run_dir
    return None


def launch(run_dir: Path, settings: Settings | None = None) -> subprocess.Popen:
    """Start the worker in its own process group (so a cancel stops everything it started)."""
    env = dict(os.environ)
    settings = settings or load_settings()
    env.update(KINN_RAW_DIR=str(settings.raw_dir), KINN_DATA_DIR=str(settings.data_dir),
               KINN_RUNS_DIR=str(settings.runs_dir))  # fmt: skip
    log = open(run_dir / "log.txt", "ab")  # noqa: SIM115 - handed to the child process
    process = subprocess.Popen(
        [sys.executable, "-m", "kinn.lab.worker", str(run_dir)],
        stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env,
        start_new_session=True,
    )  # fmt: skip
    log.close()
    tmp = run_dir / "pid.tmp"
    tmp.write_text(str(process.pid))
    os.replace(tmp, run_dir / "pid")
    return process


def cancel(run_dir: Path) -> dict:
    found = status(run_dir)
    if found.get("state") not in LIVE:
        raise LabError("This run is not running.")
    pid = pid_of(run_dir)
    if pid and alive(pid):
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(pid, signals.SIGTERM)
        deadline = time.monotonic() + 3
        while alive(pid) and time.monotonic() < deadline:
            time.sleep(0.05)
        if alive(pid):
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(pid, signals.SIGKILL)
    return set_status(run_dir, "cancelled", stage="Cancelled by the owner")


def result(run_dir: Path, name: str) -> dict | list | None:
    if name not in ("summary", "by_year", "by_stock", "equity", "lookahead", "path", "factor",
                    "sweep", "luck"):  # fmt: skip
        raise LabError("Unknown result.")
    return _read(run_dir / f"{name}.json")
