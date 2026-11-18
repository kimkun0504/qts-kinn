"""The Lab's code check: what it finds without running the code (decision 0023)."""

import pytest

from kinn.lab.check import as_dicts, check

GOOD = "def signal(data):\n    return data.close > data.close.rolling(20).mean()\n"


def found(code, **kw):
    return [(f.severity, f.line, f.message) for f in check(code, **kw)]


def test_good_code_has_nothing_to_say():
    assert check(GOOD) == []


def test_a_syntax_error_has_its_line_and_column():
    (f,) = check("def signal(data)\n    return 1\n")
    assert (f.severity, f.line, f.column) == ("error", 1, 16)
    assert f.message.startswith("Syntax error")


def test_signal_must_exist_and_take_one_argument():
    assert found("x = 1\n")[0][0] == "error"
    assert "signal(data)" in found("x = 1\n")[0][2]
    assert found("def signal(a, b):\n    return a\n")[0][:2] == ("error", 1)
    assert check("def signal(data, *, window=5):\n    return data.close > 0\n") == []
    assert found("x = 1\n", module=True) == []  # a helper module needs no signal


def test_unknown_fields_are_named_with_the_nearest_one():
    (f,) = check("def signal(data):\n    return data.closing > 0\n")
    assert f.severity == "warning" and "Did you mean data.close?" in f.message
    assert f.line == 2 and (f.column, f.end_column) == (11, 23)
    (f,) = check("def signal(d):\n    return d.volme > 0\n")  # the argument's own name
    assert "d.volume" in f.message
    assert check("def signal(data):\n    return data.close.loc[data.dates[0]] > 0\n") == []


@pytest.mark.parametrize(
    "line",
    [
        "data.close.shift(-1)",
        "data.close.shift(periods=-5)",
        "data.close.rolling(5, center=True).mean()",
    ],
)
def test_reading_later_days_is_warned(line):
    (f,) = check(f"def signal(data):\n    return {line} > 0\n")
    assert f.severity == "warning" and "later days" in f.message


def test_settings_are_checked_as_the_lab_will():
    (f,) = check('SETTINGS = {"exit": {"hold_days": 0}}\n' + GOOD)
    assert f.severity == "error" and "exit.hold_days" in f.message and f.line == 1
    assert found("SETTINGS = 3\n" + GOOD)[0][0] == "error"
    assert check("SETTINGS = make()\n" + GOOD) == []  # computed: checked when it runs


def test_helper_modules_must_be_in_the_library():
    code = "from lab.tools import zscore\nimport lab.helpers\n" + GOOD
    assert [m for _, _, m in found(code, library={"helpers"})] == [
        "There is no helper module tools in the library."
    ]
    assert check(code) == []  # library unknown: no opinion


def test_errors_come_first_and_serialise():
    findings = check("def signal(data):\n    return data.closing.shift(-1)\nSETTINGS = 2\n")
    assert findings[0].severity == "error"
    assert set(as_dicts(findings)[0]) == {"severity", "message", "line", "column", "end_line",
                                          "end_column"}  # fmt: skip
