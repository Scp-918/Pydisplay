from __future__ import annotations

from pydisplay.gui.plots.curve_config import CURVES, PLOT_GROUPS
from pydisplay.gui.plots.plot_manager import MAIN_PLOT_MIN_HEIGHT
from pydisplay.protocol.constants import ADC_VOLTS_PER_COUNT


def test_plot_groups_match_requested_grid_positions() -> None:
    groups = {group.key: group for group in PLOT_GROUPS}

    for channel in range(1, 5):
        for window_index, slots in enumerate((range(3), range(3, 6))):
            row = ((channel - 1) * 2) + window_index
            for sample_index, slot in enumerate(slots):
                assert groups[f"adc_ch{channel}_slot{slot}"].grid_position == (row, sample_index, 1, 1)


def test_plot_groups_have_expected_curves_and_subplots() -> None:
    groups = {group.key: group for group in PLOT_GROUPS}

    for channel in range(1, 5):
        for slot in range(6):
            key = f"adc_ch{channel}_slot{slot}"
            assert groups[key].curves == (key,)
            assert groups[key].subplots == ()
            assert groups[key].show_combined is True


def test_plot_groups_are_24_single_curve_panels() -> None:
    assert len(PLOT_GROUPS) == 24
    assert all(len(group.curves) == 1 for group in PLOT_GROUPS)
    assert all(group.unit == "V" for group in PLOT_GROUPS)


def test_adc_plot_curves_use_original_voltage_scale() -> None:
    assert ADC_VOLTS_PER_COUNT == 4.096 / 131_072.0
    assert all(curve.unit == "V" for curve in CURVES)
    assert all(curve.scale == ADC_VOLTS_PER_COUNT for curve in CURVES)


def test_main_plot_minimum_height_is_enlarged() -> None:
    assert MAIN_PLOT_MIN_HEIGHT >= 260


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
