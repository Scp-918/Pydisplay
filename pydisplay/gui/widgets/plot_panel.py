"""实时绘图面板。

PlotPanel 保存 ring buffer，并通过 QTimer 默认约 20 Hz 刷新 PyQtGraph 曲线。
收到 sample 时只写入 buffer；曲线刷新由定时器统一完成。

暂停绘图只停止曲线刷新，不影响串口接收和记录。
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from pydisplay.gui.plots.curve_config import CURVES
from pydisplay.gui.plots.plot_manager import PlotFpsCounter
from pydisplay.gui.plots.ring_buffer import SampleRingBuffer
from pydisplay.protocol.models import DecodedSample


class PlotPanel(QGroupBox):
    def __init__(self, *, capacity: int = 8000, refresh_hz: int = 20, window_seconds: float = 10.0) -> None:
        super().__init__("实时绘图")
        self.buffer = SampleRingBuffer(capacity)
        self.paused = False
        self.window_seconds = window_seconds
        self.fps_counter = PlotFpsCounter()
        self.plot_manager = None
        self.on_plot_frame = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        controls = QHBoxLayout()
        self.pause_checkbox = QCheckBox("暂停绘图")
        self.pause_checkbox.toggled.connect(self.set_paused)
        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(1.0, 60.0)
        self.window_spin.setDecimals(1)
        self.window_spin.setSingleStep(1.0)
        self.window_spin.setSuffix(" s")
        self.window_spin.setValue(window_seconds)
        self.window_spin.setMaximumWidth(100)
        self.window_spin.valueChanged.connect(self.set_window_seconds)
        controls.addWidget(self.pause_checkbox)
        controls.addWidget(QLabel("X轴长度"))
        controls.addWidget(self.window_spin)
        controls.addStretch(1)
        layout.addLayout(controls)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)

        plot_grid = QGridLayout()
        try:
            from pydisplay.gui.plots.plot_manager import PlotManager

            self.plot_manager = PlotManager(plot_grid, window_seconds=window_seconds)
        except Exception as exc:
            body_layout.addWidget(QLabel(f"PyQtGraph 初始化失败：{exc}"))
        else:
            body_layout.addLayout(plot_grid)

        curve_group = QGroupBox("曲线显示选项（滚动到底部勾选）")
        curve_layout = QGridLayout(curve_group)
        curve_layout.setSpacing(4)
        for index, curve in enumerate(CURVES):
            checkbox = QCheckBox(curve.label)
            checkbox.setChecked(True)
            checkbox.toggled.connect(lambda checked, key=curve.key: self.set_curve_visible(key, checked))
            curve_layout.addWidget(checkbox, index // 6, index % 6)
        body_layout.addSpacing(180)
        body_layout.addWidget(curve_group)
        body_layout.addStretch(1)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(max(1, int(1000 / refresh_hz)))
        self.timer.timeout.connect(self.refresh)
        self.timer.start()

    def add_sample(self, sample: DecodedSample) -> None:
        """追加一条 decoded sample 到绘图 ring buffer。"""
        self.buffer.append(sample)

    def set_paused(self, paused: bool) -> None:
        self.paused = paused

    def set_curve_visible(self, key: str, visible: bool) -> None:
        if self.plot_manager:
            self.plot_manager.set_curve_visible(key, visible)

    def set_window_seconds(self, window_seconds: float) -> None:
        """设置实时绘图 x 轴显示最近多少秒。"""
        self.window_seconds = float(window_seconds)
        if self.plot_manager:
            self.plot_manager.set_window_seconds(self.window_seconds)

    def refresh(self) -> None:
        """定时刷新曲线；只调用 PlotDataItem.setData()。"""
        if self.paused or self.plot_manager is None:
            return
        self.plot_manager.refresh(self.buffer)
        self.fps_counter.tick()
        if self.on_plot_frame:
            self.on_plot_frame()
