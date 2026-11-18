"""Characterise a known inference limitation; these checks do not certify executable fills.

Synthetic worlds have identical history, order, opening price and sufficient capacity.
Only the completed execution bar's later range or volume changes. It changes whether the
current proxy calls the opening fill executable. There are no observed quotes to resolve it.
"""

from kinn.validation.event_study import EXTENDED_SCHEMA, SCHEMA, summarize
from tests.test_extended_execution import walk
from tests.test_simulator import flat, session


def test_later_execution_bar_range_changes_the_inferred_opening_fill_cohort():
    quiet = session([flat(967, 10), flat(968, 10), flat(983, 10)])
    wide = session([flat(967, 10), (968, 10, 11, 9, 10, 10000), flat(983, 10)])
    assert walk(quiet)[0]
    assert not walk(wide)[0]
    # These are identical before the execution bar, including the order's reference close.
    a, b = quiet.view.symbols["AAA"], wide.view.symbols["AAA"]
    assert a.upto(967).close.tolist() == b.upto(967).close.tolist()
    assert a.open[1] == b.open[1]


def test_later_volume_changes_feasibility_even_when_both_bars_have_full_order_capacity():
    low_volume = session([flat(967, 10), (968, 10, 10.2, 9.8, 10, 10000), flat(983, 10)])
    high_volume = session([flat(967, 10), (968, 10, 10.2, 9.8, 10, 1000000), flat(983, 10)])
    assert not walk(low_volume)[0]
    entry = walk(high_volume)[0]
    assert entry and entry[0].quantity == 100
    # A 5% participation cap can accommodate the entire 100-share order in either bar.
    assert 0.05 * low_volume.view.symbols["AAA"].volume[1] >= 100


def test_empty_extended_studies_keep_the_inference_warning_and_regular_schema_stays_unchanged():
    assumptions = summarize(EXTENDED_SCHEMA.empty_table())["execution_assumptions"]
    assert assumptions["model"] == "minute_open_proxy-1"
    assert assumptions["execution_bar_statistics_affect_cap_feasibility"]
    assert not assumptions["quotes_observed"]
    assert not assumptions["signal_replay_certifies_fills"]
    assert "execution_assumptions" not in summarize(SCHEMA.empty_table())
