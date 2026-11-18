"""Checks on an algorithm's code without running it (decision 0023).

The page calls these as the owner types, and a run is refused while an error remains. They read
the code with :mod:`ast` only: nothing here imports or executes it.

- **Errors** stop a run: a syntax error, no ``signal(data)``, a ``SETTINGS`` the Lab refuses.
- **Warnings** do not: a ``data.<name>`` that is not a field (with the nearest field named), a
  ``shift`` by a negative number or a centered window (both read later days, which the lookahead
  test would mark), an import of a helper module (``lab.<name>``) that is not in the library.
"""

from __future__ import annotations

import ast
import difflib
from dataclasses import asdict, dataclass

from kinn.lab.data import FIELDS
from kinn.lab.settings import SettingsError, parse

DATA_ATTRIBUTES = set(FIELDS) | {"fields", "dates", "stocks"}
ENTRY_POINTS = ("signal", "exit_signal")


@dataclass(frozen=True)
class Finding:
    severity: str  # "error" or "warning"
    message: str
    line: int  # 1-based
    column: int  # 0-based, as Python counts
    end_line: int
    end_column: int


def _at(node: ast.AST, severity: str, message: str) -> Finding:
    line = getattr(node, "lineno", 1)
    column = getattr(node, "col_offset", 0)
    end_line = getattr(node, "end_lineno", None) or line
    end_column = getattr(node, "end_col_offset", None) or column + 1
    return Finding(severity, message, line, column, end_line, end_column)


def _syntax(error: SyntaxError, code: str) -> Finding:
    line = error.lineno or 1
    lines = code.splitlines() or [""]
    text = lines[min(line, len(lines)) - 1]
    column = max((error.offset or 1) - 1, 0)
    end_line = error.end_lineno or line
    end_column = (error.end_offset or 0) - 1 if error.end_offset else min(column + 1, len(text))
    if end_line == line and end_column <= column:
        end_column = min(column + 1, max(len(text), column + 1))
    return Finding("error", f"Syntax error: {error.msg}", line, column, end_line, end_column)


def _negative(node: ast.AST) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        operand = node.operand
        return isinstance(operand, ast.Constant) and isinstance(operand.value, int | float)
    if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
        return False
    return isinstance(node.value, int | float) and node.value < 0


def check(code: str, library: set[str] | None = None, *, module: bool = False) -> list[Finding]:
    """Every problem found in ``code``, errors first, then by line. ``library`` is the names of
    the owner's helper modules, when known. ``module``: the code is a helper module, which needs
    no ``signal``."""
    try:
        tree = ast.parse(code, filename="algorithm.py")
    except SyntaxError as error:
        return [_syntax(error, code)]
    findings: list[Finding] = []
    top = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assigned = {t.id for node in tree.body if isinstance(node, ast.Assign)
                for t in node.targets if isinstance(t, ast.Name)}  # fmt: skip

    if not module and "signal" not in top and "signal" not in assigned:
        message = ("Define a function signal(data) that returns a table of True/False (or "
                   "scores) by date and stock.")  # fmt: skip
        findings.append(Finding("error", message, 1, 0, 1, 1))
    data_names = {"data"}
    for name in ENTRY_POINTS:
        node = top.get(name)
        if node is None:
            continue
        args = node.args
        positional = len(args.posonlyargs) + len(args.args)
        if positional != 1 or args.vararg or args.kwonlyargs and any(
            d is None for d in args.kw_defaults
        ):  # fmt: skip
            findings.append(_at(node, "error", f"{name} takes one argument: {name}(data)."))
        if positional:
            data_names.add((args.posonlyargs + args.args)[0].arg)

    for node in ast.walk(tree):
        # SETTINGS: checked as the Lab will check it, when it is a plain literal.
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "SETTINGS" for t in node.targets
        ):  # fmt: skip
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                continue  # computed: the worker checks it when it runs
            if not isinstance(value, dict):
                findings.append(_at(node.value, "error", "SETTINGS must be a dict, for example "
                                    "{'exit': {'hold_days': 20}}."))  # fmt: skip
                continue
            try:
                parse(None, value)
            except SettingsError as error:
                findings.append(_at(node.value, "error", f"SETTINGS: {error}."))
        # data.<field>
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                and node.value.id in data_names and node.attr not in DATA_ATTRIBUTES:  # fmt: skip
            near = difflib.get_close_matches(node.attr, sorted(DATA_ATTRIBUTES), n=1)
            hint = f" Did you mean {node.value.id}.{near[0]}?" if near else ""
            findings.append(_at(node, "warning", f"{node.value.id}.{node.attr} is not a field."
                                f"{hint} The Data tab lists them."))  # fmt: skip
        # Reading later days.
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method == "shift":
                first = node.args[0] if node.args else next(
                    (k.value for k in node.keywords if k.arg == "periods"), None)  # fmt: skip
                if first is not None and _negative(first):
                    findings.append(_at(node, "warning", "A negative shift reads later days. "
                                        "The lookahead test will mark the run."))  # fmt: skip
            elif method == "rolling" and any(
                k.arg == "center" and isinstance(k.value, ast.Constant) and k.value.value is True
                for k in node.keywords
            ):  # fmt: skip
                findings.append(_at(node, "warning", "A centered window reads later days. "
                                    "The lookahead test will mark the run."))  # fmt: skip
        # Helper modules: ``import lab.<module>`` or ``from lab import <module>``.
        elif library is not None and isinstance(node, ast.Import | ast.ImportFrom):
            wanted = []
            if isinstance(node, ast.Import):
                wanted = [a.name.split(".")[1] for a in node.names if a.name.startswith("lab.")]
            elif node.module == "lab":
                wanted = [a.name for a in node.names]
            elif (node.module or "").startswith("lab."):
                wanted = [node.module.split(".")[1]]
            for module in wanted:
                if module not in library:
                    findings.append(_at(node, "warning", f"There is no helper module {module} "
                                        "in the library."))  # fmt: skip
    findings.sort(key=lambda f: (f.severity != "error", f.line, f.column))
    return findings


def as_dicts(findings: list[Finding]) -> list[dict]:
    return [asdict(f) for f in findings]
