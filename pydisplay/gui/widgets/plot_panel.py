"""实时绘图面板。

PlotPanel 保存 ring buffer，并通过 QTimer 默认约 20 Hz 刷新 PyQtGraph 曲线。
收到 sample 时只写入 buffer；曲线刷新由定时器统一完成。

暂停绘图只停止曲线刷新，不影响串口接收和记录。
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QGridLayout, QGroupBox, QLabel, QVBoxLayout

from pydisplay.gui.plots.curve_config import CURVES
from pydisplay.gui.plots.plot_manager import PlotFpsCounter
from pydisplay.gui.plots.ring_buffer import SampleRingBuffer
from pydisplay.protocol.models import DecodedSample


class PlotPanel(QGroupBox):
    def __init__(self, *, capacity: int = 4000, refresh_hz: int = 20, window_seconds: float = 10.0) -> None:
        super().__init__("实时绘图")
        self.buffer = SampleRingBuffer(capacity)
        self.paused = False
        self.fps_counter = PlotFpsCounter()
        self.plot_manager = None
        self.on_plot_frame = None

        layout = QVBoxLayout(self)
        controls = QGridLayout()
        self.pause_checkbox = QCheckBox("暂停绘图")
        self.pause_checkbox.toggled.connect(self.set_paused)
        controls.addWidget(self.pause_checkbox, 0, 0)
        for index, curve in enumerate(CURVES, start=1):
            checkbox = QCheckBox(curve.label)
            checkbox.setChecked(True)
            checkbox.toggled.connect(lambda checked, key=curve.key: self.set_curve_visible(key, checked))
            controls.addWidget(checkbox, index // 6, index % 6)
        layout.addLayout(controls)

        plot_grid = QGridLayout()
        try:
            from pydisplay.gui.plots.plot_manager import PlotManager

            self.plot_manager = PlotManager(plot_grid, window_seconds=window_seconds)
            layout.addLayout(plot_grid)
        except Exception as exc:
            layout.addWidget(QLabel(f"PyQtGraph 初始化失败：{exc}"))

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

    def refresh(self) -> None:
        """定时刷新曲线；只调用 PlotDataItem.setData()。"""
        if self.paused or self.plot_manager is None:
            return
        self.plot_manager.refresh(self.buffer)
        self.fps_counter.tick()
        if self.on_plot_frame:
            self.on_plot_frame()
