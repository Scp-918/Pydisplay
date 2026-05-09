"""下位机控制面板。

用户在这里选择 PPG mode、LED 亮度、量程、脉宽和 k 值。
面板本身不拼接 bytes，只生成 ControlMetadata，通过 signal 交给主窗口。
最终命令编码由 `pydisplay.protocol.commands` 完成。
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QPushButton, QSpinBox, QVBoxLayout

from pydisplay.protocol.models import ControlMetadata


class ControlPanel(QGroupBox):
    control_command_requested = Signal(object)
    k_value_changed = Signal(float)

    def __init__(self) -> None:
        super().__init__("下位机控制")
        self.k_spin = QDoubleSpinBox()
        self.k_spin.setRange(-1000.0, 1000.0)
        self.k_spin.setDecimals(6)
        self.k_spin.setValue(5.0)
        self.k_spin.valueChanged.connect(self.k_value_changed)

        self.mode_combo = _combo([("MultiLED", 0x01), ("HR", 0x02), ("SpO2", 0x03)])
        self.submode_combo = _combo([("G-R-IR", 0x01), ("G", 0x02), ("R", 0x03), ("IR", 0x04), ("R-IR", 0x05)])
        self.led_g = _spin(0, 9, 1)
        self.led_r = _spin(0, 9, 1)
        self.led_ir = _spin(0, 9, 1)
        self.ppg_range = _combo([("1", 0x01), ("2", 0x02), ("3", 0x03), ("4", 0x04)])
        self.pulse_width = _combo([("1", 0x01), ("2", 0x02), ("3", 0x03), ("4", 0x04)])
        self.gyro_range = _combo([("245 dps", 0x01), ("500 dps", 0x02), ("2000 dps", 0x03)])
        self.accel_range = _combo([("2 g", 0x01), ("4 g", 0x02), ("8 g", 0x03), ("16 g", 0x04)])

        send_button = QPushButton("发送控制命令")
        send_button.clicked.connect(self._emit_command)

        form = QFormLayout()
        for label, widget in (
            ("k 值", self.k_spin),
            ("PPG mode", self.mode_combo),
            ("Multi sub-mode", self.submode_combo),
            ("绿光 LED", self.led_g),
            ("红光 LED", self.led_r),
            ("IR LED", self.led_ir),
            ("PPG 量程", self.ppg_range),
            ("脉宽", self.pulse_width),
            ("陀螺仪量程", self.gyro_range),
            ("加速度量程", self.accel_range),
        ):
            form.addRow(label, widget)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(send_button)

    def _emit_command(self) -> None:
        """收集 GUI 控件当前值，组装成 ControlMetadata。"""
        self.control_command_requested.emit(
            ControlMetadata(
                ppg_mode=self.mode_combo.currentData(),
                ppg_multi_submode=self.submode_combo.currentData(),
                led_green=self.led_g.value(),
                led_red=self.led_r.value(),
                led_ir=self.led_ir.value(),
                ppg_adc_range=self.ppg_range.currentData(),
                ppg_pulse_width=self.pulse_width.currentData(),
                gyro_range=self.gyro_range.currentData(),
                accel_range=self.accel_range.currentData(),
            )
        )


def _combo(items: list[tuple[str, int]]) -> QComboBox:
    combo = QComboBox()
    for label, value in items:
        combo.addItem(label, value)
    return combo


def _spin(minimum: int, maximum: int, value: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(minimum, maximum)
    spin.setValue(value)
    return spin
