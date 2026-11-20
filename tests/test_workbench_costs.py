"""The cost calculator charges what the Lab charges."""

import pytest

from apps.workbench import costs
from kinn.costs.model import load
from kinn.lab.engine import Costs


def test_each_leg_costs_what_the_lab_charges():
    lab = Costs(load(costs.MODEL))
    out = costs.estimate({"price": "20", "value": "2000", "adv": "5000000"})
    buy, sell = out["legs"]
    for leg, auction in ((buy, True), (sell, True)):
        fees, slippage = lab.side(side=leg["side"], price=20, value=leg["value"], adv=5e6,
                                  auction=auction)  # fmt: skip
        assert leg["commission"] + leg["fees"] == pytest.approx(fees)
        assert leg["slippage"] == pytest.approx(slippage)
    assert out["cost_2x"] - out["cost"] == pytest.approx(buy["slippage"] + sell["slippage"])
    assert out["bps"] == pytest.approx(out["cost"] / 2000 * 1e4)


def test_a_short_sells_first_and_a_marketable_fill_pays_the_spread():
    out = costs.estimate({"price": "4", "value": "2000", "adv": "300000", "side": "short",
                          "entry": "marketable", "exit": "auction"})  # fmt: skip
    opening, closing = out["legs"]
    assert (opening["side"], closing["side"]) == ("sell", "buy")
    assert opening["slippage"] == pytest.approx(out["half_spread_bps"] / 1e4 * opening["value"])
    cheap = {row["price"]: row["bps"] for row in out["prices"]}
    assert cheap[1] > cheap[5] > cheap[100]


@pytest.mark.parametrize(
    ("query", "words"),
    [
        ({"value": "2000"}, "Price is required"),
        ({"price": "x", "value": "1"}, "Price must be"),
        ({"price": "5", "value": "2000", "entry": "dark pool"}, "auction"),
    ],
)
def test_bad_inputs_are_named(query, words):
    with pytest.raises(costs.CostError, match=words):
        costs.estimate(query)
