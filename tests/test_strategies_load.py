"""Every strategy folder loads and declares what the run entry point needs."""

from pathlib import Path

import pytest
import yaml

from kinn import run as runner
from kinn.costs import model as cost_model

STRATEGIES = Path(__file__).resolve().parents[1] / "strategies"
NAMES = sorted(p.parent.name for p in STRATEGIES.glob("*/strategy.py"))


@pytest.mark.parametrize("name", NAMES)
def test_strategy_loads_with_each_of_its_configs(name):
    meta = yaml.safe_load((STRATEGIES / name / "strategy.yaml").read_text())
    assert meta["name"] == name and meta["family"] is not None
    cost_model.load(meta["cost_calibration"])
    assert (STRATEGIES / name / "HYPOTHESIS.md").exists(), "write the hypothesis first"
    configs = sorted((STRATEGIES / name / "configs").glob("*.yaml"))
    assert configs
    for config in configs:
        cfg = yaml.safe_load(config.read_text())
        strategy = runner.load_strategy(name, cfg.get("params", {}))
        assert strategy.name == name and strategy.universe.where()
