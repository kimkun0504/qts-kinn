"""Every book config and every daily alpha loads."""

from pathlib import Path

import pytest
import yaml

from kinn import book_run

ROOT = Path(__file__).resolve().parents[1]
BOOKS = sorted(p.stem for p in (ROOT / "books").glob("*.yaml"))
ALPHAS = sorted(p.parent.name for p in (ROOT / "strategies").glob("*/alpha.py"))


@pytest.mark.parametrize("name", BOOKS)
def test_book_config_builds_its_models(name):
    cfg = book_run.load_book(name)
    parts = book_run.parts_of(cfg)
    assert parts["alphas"] and cfg["family"] and cfg["cost_calibration"]
    assert parts["universe"].where()


@pytest.mark.parametrize("name", ALPHAS)
def test_alpha_folder_declares_what_a_book_needs(name):
    folder = ROOT / "strategies" / name
    meta = yaml.safe_load((folder / "strategy.yaml").read_text())
    assert meta["name"] == name and meta["kind"] == "forecast" and meta["family"]
    assert (folder / "HYPOTHESIS.md").exists(), "write the hypothesis first"
    alpha = book_run.load_alpha(name, {})
    assert alpha.name == name and alpha.lookback > 0


def test_a_config_that_swaps_the_constructor_does_not_inherit_the_other_kinds_settings():
    ranked = book_run.load_book("momentum_dev_ranked")
    assert ranked["portfolio"] == {"kind": "ranked", "count": 15}
    assert ranked["limits"]["gross"] == 1.5 and ranked["rebalance"] == "monthly"
