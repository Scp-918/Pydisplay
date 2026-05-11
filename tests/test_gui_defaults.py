from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from pydisplay.config import DEFAULT_K_VALUE, DEFAULT_PLOT_WINDOW_SECONDS
from pydisplay.gui.widgets.control_panel import ControlPanel
from pydisplay.gui.widgets.health_panel import HealthPanel
from pydisplay.gui.widgets.plot_panel import PlotPanel
from pydisplay.protocol.models import DecodedSample
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


def test_plot_panel_clear_button_empties_current_plot_buffer(qtbot) -> None:
    panel = PlotPanel()
    qtbot.addWidget(panel)
    panel.add_sample(
        DecodedSample(
            timestamp_pc_ns=1,
            relative_time_s=0.0,
            frame_seq=1,
            sample_seq=1,
            ppg_g=1,
            ppg_r=2,
            ppg_ir=3,
            acc_x=0,
            acc_y=0,
            acc_z=1,
            gyro_x=0,
            gyro_y=0,
            gyro_z=0,
            uh1=1,
            uh2=2,
            uh3=3,
            uh4=4,
            uc1=0.5,
            uc2=1,
            uc3=1.5,
            uc4=2,
            ud1=0.25,
            ud2=0.4,
        )
    )

    assert len(panel.buffer) == 1
    panel.clear_button.click()

    assert len(panel.buffer) == 0


def test_health_panel_widens_realtime_metric_fields(qtbot) -> None:
    panel = HealthPanel()
    qtbot.addWidget(panel)

    for key in ("valid_frame_rate", "parser_buffer_bytes", "lost_frames", "lost_frame_ratio", "last_error"):
        assert panel.labels[key].minimumWidth() >= 210
    assert panel.labels["last_error"].wordWrap() is True
