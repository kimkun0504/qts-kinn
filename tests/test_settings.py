from datetime import date
from pathlib import Path

import pytest

from kinn.core import settings as s


def test_holdout_start_is_the_fixed_date():
    assert date(2023, 11, 9) == s.HOLDOUT_START


def test_holdout_start_cannot_be_moved_by_the_environment(tmp_path):
    env = {"KINN_HOLDOUT_START": "2030-01-01", "KINN_RUNS_DIR": str(tmp_path)}
    s.load_settings(env)
    assert date(2023, 11, 9) == s.HOLDOUT_START
    assert not hasattr(s.Settings, "holdout_start")


def test_paths_come_from_the_environment(tmp_path):
    env = {
        "KINN_RAW_DIR": str(tmp_path / "raw"),
        "KINN_DATA_DIR": str(tmp_path / "processed"),
        "KINN_RUNS_DIR": str(tmp_path / "runs"),
    }
    got = s.load_settings(env)
    assert got.raw_dir == (tmp_path / "raw").resolve()
    assert got.data_dir == (tmp_path / "processed").resolve()
    assert got.runs_dir == (tmp_path / "runs").resolve()


def test_default_runs_dir_sits_beside_the_repo():
    repo_root = Path(__file__).resolve().parents[1]
    assert s.load_settings({}).runs_dir == repo_root.parent / "runs"


@pytest.mark.parametrize("name", ["KINN_RAW_DIR", "KINN_DATA_DIR", "KINN_RUNS_DIR"])
def test_a_path_inside_a_sealed_folder_is_refused(tmp_path, name):
    env = {
        "KINN_RAW_DIR": str(tmp_path / "raw"),
        "KINN_DATA_DIR": str(tmp_path / "processed"),
        "KINN_RUNS_DIR": str(tmp_path / "runs"),
        name: str(tmp_path / "sealed" / "massive"),
    }
    with pytest.raises(s.SettingsError, match="sealed"):
        s.load_settings(env)


@pytest.mark.parametrize("name", ["KINN_DATA_DIR", "KINN_RUNS_DIR"])
def test_writing_inside_the_raw_folder_is_refused(tmp_path, name):
    env = {
        "KINN_RAW_DIR": str(tmp_path / "raw"),
        "KINN_DATA_DIR": str(tmp_path / "processed"),
        "KINN_RUNS_DIR": str(tmp_path / "runs"),
        name: str(tmp_path / "raw" / "derived"),
    }
    with pytest.raises(s.SettingsError, match="read-only raw"):
        s.load_settings(env)
