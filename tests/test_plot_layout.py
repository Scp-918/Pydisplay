from __future__ import annotations

from pydisplay.gui.plots.curve_config import CURVES, PLOT_GROUPS


def test_plot_groups_match_requested_grid_positions() -> None:
    groups = {group.key: group for group in PLOT_GROUPS}

    assert groups["adc_ch1"].grid_position == (0, 0, 1, 1)
    assert groups["adc_ch2"].grid_position == (0, 1, 1, 1)
    assert groups["adc_ch3"].grid_position == (1, 0, 1, 1)
    assert groups["adc_ch4"].grid_position == (1, 1, 1, 1)


def test_plot_groups_have_expected_curves_and_subplots() -> None:
    groups = {group.key: group for group in PLOT_GROUPS}

    for channel in range(1, 5):
        key = f"adc_ch{channel}"
        expected = tuple(f"adc_ch{channel}_slot{slot}" for slot in range(6))
        assert groups[key].curves == expected
        assert groups[key].subplots == ()
        assert groups[key].show_combined is True


def test_all_plot_group_curve_keys_are_known() -> None:
    known_keys = {curve.key for curve in CURVES}
    grouped_keys = {key for group in PLOT_GROUPS for key in group.curves}
    subplot_grouped_keys = {key for group in PLOT_GROUPS for subplot in group.subplot_groups for key in subplot.curves}

    assert grouped_keys <= known_keys
    assert subplot_grouped_keys <= known_keys
    assert len(known_keys) == len(CURVES)


def test_plot_group_titles_do_not_include_grid_letters() -> None:
    for group in PLOT_GROUPS:
        assert not group.title.startswith(("a.", "b.", "c.", "d.", "e.", "f.", "g."))


def test_requested_curve_colors_are_distinct_and_muted() -> None:
    colors = {curve.key: curve.color for curve in CURVES}

    assert colors["adc_ch1_slot0"] == "#4C78A8"
    assert colors["adc_ch2_slot3"] == "#D08A3C"
    assert colors["adc_ch4_slot5"] == "#7A68A6"
