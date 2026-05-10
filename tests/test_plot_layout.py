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
    assert groups["ppg"].show_combined is False
    assert groups["uh23"].curves == ("uh2", "uh3")
    assert groups["uh23"].subplots == ("uh2", "uh3")
    assert groups["uh23"].show_combined is False
    assert groups["uc23"].curves == ("uc2", "uc3")
    assert groups["uc23"].subplots == ("uc2", "uc3")
    assert groups["uc23"].show_combined is False
    assert groups["ud"].curves == ("ud1", "ud2")
    assert groups["ud"].subplots == ("ud1", "ud2")
    assert groups["ud"].show_combined is False
    assert groups["sensor14"].curves == ("uh1", "uc1", "uh4", "uc4")
    assert groups["sensor14"].subplots == ()
    assert groups["sensor14"].show_combined is True


def test_all_plot_group_curve_keys_are_known() -> None:
    known_keys = {curve.key for curve in CURVES}
    grouped_keys = {key for group in PLOT_GROUPS for key in group.curves}

    assert grouped_keys <= known_keys
    assert len(known_keys) == len(CURVES)


def test_plot_group_titles_do_not_include_grid_letters() -> None:
    for group in PLOT_GROUPS:
        assert not group.title.startswith(("a.", "b.", "c.", "d.", "e.", "f.", "g."))


def test_requested_curve_colors_are_distinct_and_muted() -> None:
    colors = {curve.key: curve.color for curve in CURVES}

    assert colors["ppg_g"] == "#3E8F5C"
    assert colors["ppg_r"] == "#B94E4E"
    assert colors["ppg_ir"] == "#7A68A6"
    assert colors["uh2"] == "#B65C5A"
    assert colors["uh3"] == "#C87A3A"
    assert colors["uc2"] == "#4C78A8"
    assert colors["uc3"] == "#3F9C9A"
    assert colors["ud1"] == "#BFA43A"
    assert colors["ud2"] == "#D08A3C"
