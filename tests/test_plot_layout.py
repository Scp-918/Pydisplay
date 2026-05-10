from __future__ import annotations

from pydisplay.gui.plots.curve_config import CURVES, PLOT_GROUPS


def test_plot_groups_match_requested_grid_positions() -> None:
    groups = {group.key: group for group in PLOT_GROUPS}

    assert groups["ppg"].grid_position == (0, 0, 2, 1)
    assert groups["uh23"].grid_position == (0, 1, 2, 1)
    assert groups["uc23"].grid_position == (0, 2, 1, 1)
    assert groups["ud"].grid_position == (1, 2, 1, 1)
    assert groups["acc"].grid_position == (2, 0, 1, 1)
    assert groups["gyro"].grid_position == (2, 1, 1, 1)
    assert groups["sensor14"].grid_position == (2, 2, 1, 1)


def test_plot_groups_have_expected_curves_and_subplots() -> None:
    groups = {group.key: group for group in PLOT_GROUPS}

    assert groups["ppg"].curves == ("ppg_g", "ppg_r", "ppg_ir")
    assert groups["ppg"].subplots == ("ppg_g", "ppg_r", "ppg_ir")
    assert groups["uh23"].curves == ("uh2", "uh3")
    assert groups["uh23"].subplots == ("uh2", "uh3")
    assert groups["uc23"].curves == ("uc2", "uc3")
    assert groups["uc23"].subplots == ("uc2", "uc3")
    assert groups["ud"].curves == ("ud1", "ud2")
    assert groups["ud"].subplots == ("ud1", "ud2")
    assert groups["sensor14"].curves == ("uh1", "uc1", "uh4", "uc4")
    assert groups["sensor14"].subplots == ()


def test_all_plot_group_curve_keys_are_known() -> None:
    known_keys = {curve.key for curve in CURVES}
    grouped_keys = {key for group in PLOT_GROUPS for key in group.curves}

    assert grouped_keys <= known_keys
    assert len(known_keys) == len(CURVES)
