"""Rules about the repository itself: import direction, the legacy name, the sandbox."""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CODE_DIRS = ("src", "strategies", "apps", "tests")


def _python_files():
    for folder in CODE_DIRS:
        for path in (REPO / folder).rglob("*.py"):
            if "node_modules" not in path.parts:
                yield path


def test_import_rules_hold():
    lint = Path(sys.executable).with_name("lint-imports")
    done = subprocess.run([str(lint)], cwd=REPO, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr


def test_the_legacy_package_name_is_never_used():
    legacy = "q" + "ts"  # spelled this way so this file passes its own check
    pattern = re.compile(rf"(?<![\w-]){legacy}(?![\w-])")
    hits = [
        f"{path.relative_to(REPO)}:{number}"
        for path in _python_files()
        for number, line in enumerate(path.read_text().splitlines(), 1)
        if pattern.search(line)
    ]
    assert not hits, f"legacy name used in: {hits}"


def test_no_absolute_user_paths_in_code():
    pattern = re.compile(r"/(Users|home)/\w+")
    hits = [
        str(path.relative_to(REPO)) for path in _python_files() if pattern.search(path.read_text())
    ]
    assert not hits, f"hard-coded absolute path in: {hits}"


def test_the_research_sandbox_is_not_a_package():
    assert not (REPO / "research" / "__init__.py").exists()


def test_gitignore_hides_no_source_file():
    """A broad ignore pattern once hid src/kinn/data from git."""
    done = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard", *CODE_DIRS],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    hidden = [
        line
        for line in done.stdout.splitlines()
        if not any(
            part in line
            for part in ("__pycache__", ".egg-info", "_cache", "node_modules/", "web/dist/")
        )
    ]
    assert not hidden, f"ignored by git: {hidden}"


def test_the_snapshot_split_factor_is_used_only_by_the_data_build():
    """Decision 0015: `unadjust` reveals later splits; only the build may read it."""
    root = Path(__file__).resolve().parents[1]
    allowed = {"src/kinn/data/sharadar.py", "src/kinn/data/build.py"}
    users = {
        str(path.relative_to(root))
        for folder in ("src", "apps", "strategies")
        for path in (root / folder).rglob("*.py")
        if "node_modules" not in path.parts and "unadjust" in path.read_text()
    }
    assert users <= allowed
