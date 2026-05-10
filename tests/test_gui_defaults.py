from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from pydisplay.config import DEFAULT_K_VALUE, DEFAULT_PLOT_WINDOW_SECONDS
from pydisplay.gui.widgets.control_panel import ControlPanel
from pydisplay.gui.widgets.health_panel import HealthPanel
from pydisplay.gui.widgets.plot_panel import PlotPanel
from pydisplay.protocol.constants import (
    DEFAULT_ACCEL_RANGE,
    DEFAULT_GYRO_RANGE,
    DEFAULT_LED_GREEN,
    DEFAULT_LED_IR,
    DEFAULT_LED_RED,
    DEFAULT_PPG_ADC_RANGE,
    DEFAULT_PPG_MODE,
    DEFAULT_PPG_MULTI_SUBMODE,
    DEFAULT_PPG_PULSE_WIDTH,
)


def test_control_panel_defaults_match_firmware_initial_parameters(qtbot) -> None:
    panel = ControlPanel()
    qtbot.addWidget(panel)

    assert panel.k_spin.value() == pytest.approx(DEFAULT_K_VALUE)
    assert panel.mode_combo.currentData() == DEFAULT_PPG_MODE
    assert panel.submode_combo.currentData() == DEFAULT_PPG_MULTI_SUBMODE
    assert panel.led_g.value() == DEFAULT_LED_GREEN
    assert panel.led_r.value() == DEFAULT_LED_RED
    assert panel.led_ir.value() == DEFAULT_LED_IR
    assert panel.ppg_range.currentData() == DEFAULT_PPG_ADC_RANGE
    assert panel.pulse_width.currentData() == DEFAULT_PPG_PULSE_WIDTH
    assert panel.gyro_range.currentData() == DEFAULT_GYRO_RANGE
    assert panel.accel_range.currentData() == DEFAULT_ACCEL_RANGE


def test_plot_panel_defaults_to_five_second_window(qtbot) -> None:
    panel = PlotPanel()
    qtbot.addWidget(panel)

    assert panel.window_seconds == pytest.approx(DEFAULT_PLOT_WINDOW_SECONDS)
    assert panel.window_spin.value() == pytest.approx(DEFAULT_PLOT_WINDOW_SECONDS)


def test_health_panel_widens_realtime_metric_fields(qtbot) -> None:
    panel = HealthPanel()
    qtbot.addWidget(panel)

    for key in ("valid_frame_rate", "parser_buffer_bytes", "last_error"):
        assert panel.labels[key].minimumWidth() >= 210
    assert panel.labels["last_error"].wordWrap() is True
