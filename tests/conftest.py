from __future__ import annotations

import pytest

from kinn.core.settings import load_settings
from kinn.data import build
from tests import synthetic_raw


def _build(tmp, **raw_options):
    raw_dir = synthetic_raw.make_raw(tmp / "raw", **raw_options)
    settings = load_settings(
        {
            "KINN_RAW_DIR": str(raw_dir),
            "KINN_DATA_DIR": str(tmp / "processed"),
            "KINN_RUNS_DIR": str(tmp / "runs"),
        }
    )
    assert build.build_bars(settings, budget_seconds=120, workers=2)[1] == 0
    build_id, pending = build.build_tables(settings)
    assert not pending
    return settings


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Settings for a complete build over the synthetic raw folder."""
    return _build(tmp_path_factory.mktemp("full"))


@pytest.fixture(scope="session")
def build_synthetic(tmp_path_factory):
    """A function that builds a variant of the synthetic raw folder."""
    return lambda name, **options: _build(tmp_path_factory.mktemp(name), **options)
