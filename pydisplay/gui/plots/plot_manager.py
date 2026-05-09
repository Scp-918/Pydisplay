"""PyQtGraph 曲线管理器。

初始化时创建所有 PlotWidget 和 PlotDataItem。
刷新时只调用已有曲线的 setData()，避免每帧创建新曲线导致卡顿。
"""

from __future__ import annotations

from collections import defaultdict
import time

from .curve_config import CURVES, CurveConfig
from .ring_buffer import SampleRingBuffer


class PlotManager:
    """持有所有曲线对象，并集中刷新。"""

    def __init__(self, layout, *, window_seconds: float = 10.0) -> None:
        import pyqtgraph as pg

        self.window_seconds = window_seconds
        self.visible: dict[str, bool] = {curve.key: True for curve in CURVES}
        self.curves = {}
        self.plot_widgets = {}
        grouped: dict[str, list[CurveConfig]] = defaultdict(list)
        for curve in CURVES:
            grouped[curve.group].append(curve)

        for row, (group, configs) in enumerate(grouped.items()):
            plot = pg.PlotWidget(title=group)
            plot.showGrid(x=True, y=True, alpha=0.2)
            plot.setLabel("bottom", "时间", units="s")
            if configs:
                plot.setLabel("left", group, units=configs[0].unit)
            plot.addLegend()
            layout.addWidget(plot, row // 2, row % 2)
            self.plot_widgets[group] = plot
            for config in configs:
                item = plot.plot(name=config.label, pen=pg.mkPen(config.color, width=1.2))
                self.curves[config.key] = item

    def set_curve_visible(self, key: str, visible: bool) -> None:
        self.visible[key] = visible
        if key in self.curves:
            self.curves[key].setVisible(visible)

    def refresh(self, buffer: SampleRingBuffer) -> None:
        """按当前可见性从 ring buffer 读取数据并刷新曲线。"""
        for key, item in self.curves.items():
            if not self.visible.get(key, True):
                continue
            x, y = buffer.get_series(key, self.window_seconds)
            item.setData(x, y)


class PlotFpsCounter:
    def __init__(self) -> None:
        self.frames = 0
        self.last_time = time.monotonic()
        self.fps = 0.0

    def tick(self) -> float:
        self.frames += 1
        now = time.monotonic()
        elapsed = now - self.last_time
        if elapsed >= 1.0:
            self.fps = self.frames / elapsed
            self.frames = 0
            self.last_time = now
        return self.fps
